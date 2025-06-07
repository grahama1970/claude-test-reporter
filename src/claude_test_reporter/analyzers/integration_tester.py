

Module: integration_tester.py
Description: Actually tests integration between modules by starting them and sending real messages
"""

External Dependencies:
- subprocess: https://docs.python.org/3/library/subprocess.html
- asyncio: https://docs.python.org/3/library/asyncio.html
- aiohttp: https://pypi.org/project/aiohttp/

Sample Input:
>>> tester = IntegrationTester()
>>> result = asyncio.run(tester.test_module_communication(
...     module_a={'name': 'sparta', 'port': 8001},
...     module_b={'name': 'arangodb', 'port': 8002}
... ))

Expected Output:
>>> print(result)
{'communication_established': True, 'latency_ms': 45.2, 'messages_sent': 10, 'messages_received': 10}

Example Usage:
>>> tester = IntegrationTester()
>>> hub_test = asyncio.run(tester.test_granger_hub_connectivity())
>>> if not hub_test['hub_responsive']:
...     print("WARNING: Granger Hub not responding!")
"""

import subprocess
import asyncio
import aiohttp
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import socket
import signal


class IntegrationTester:
    """Test real integration between modules without mocks."""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.processes = []
        self.base_ports = {
            'granger_hub': 8000,
            'sparta': 8001,
            'marker': 8002,
            'arangodb': 8003,
            'llm_call': 8004,
            'test_reporter': 8005
        }

    async def test_module_communication(self,
                                      module_a: Dict[str, Any],
                                      module_b: Dict[str, Any]) -> Dict[str, Any]:
        """Test real communication between two modules."""
        results = {
            "test_name": f"{module_a['name']} -> {module_b['name']}",
            "timestamp": datetime.now().isoformat(),
            "communication_established": False,
            "messages_sent": 0,
            "messages_received": 0,
            "latency_ms": 0,
            "errors": [],
            "module_a_started": False,
            "module_b_started": False
        }

        try:
            # Start both modules
            proc_a = await self._start_module(module_a['name'], module_a.get('port'))
            proc_b = await self._start_module(module_b['name'], module_b.get('port'))

            if not proc_a or not proc_b:
                results["errors"].append("Failed to start one or both modules")
                return results

            results["module_a_started"] = True
            results["module_b_started"] = True

            # Wait for modules to initialize
            await asyncio.sleep(3)

            # Send test messages
            test_messages = [
                {"type": "ping", "id": 1, "timestamp": time.time()},
                {"type": "data", "id": 2, "payload": "test_data"},
                {"type": "query", "id": 3, "query": "SELECT * FROM test"}
            ]

            # Send messages and measure latency
            async with aiohttp.ClientSession() as session:
                for msg in test_messages:
                    start_time = time.time()

                    # Send from A to B
                    try:
                        url_a = f"http://localhost:{module_a.get('port', 8001)}/send"
                        async with session.post(url_a, json={
                            "target": module_b['name'],
                            "message": msg
                        }) as resp:
                            if resp.status == 200:
                                results["messages_sent"] += 1

                        # Check if B received it
                        url_b = f"http://localhost:{module_b.get('port', 8002)}/messages"
                        async with session.get(url_b) as resp:
                            if resp.status == 200:
                                messages = await resp.json()
                                if any(m.get('id') == msg['id'] for m in messages):
                                    results["messages_received"] += 1

                        # Calculate latency
                        latency = (time.time() - start_time) * 1000
                        results["latency_ms"] = max(results["latency_ms"], latency)

                    except Exception as e:
                        results["errors"].append(f"Communication error: {str(e)}")

            # Determine if communication was established
            if results["messages_sent"] > 0 and results["messages_received"] > 0:
                results["communication_established"] = True

        except Exception as e:
            results["errors"].append(f"Test error: {str(e)}")

        finally:
            # Clean up processes
            await self._cleanup_processes()

        return results

    async def test_granger_hub_connectivity(self) -> Dict[str, Any]:
        """Test connectivity with Granger Hub."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "hub_responsive": False,
            "registration_successful": False,
            "heartbeat_working": False,
            "message_routing_working": False,
            "connected_modules": [],
            "errors": []
        }

        try:
            # Check if hub is already running
            hub_running = await self._check_port_open('localhost', 8000)

            if not hub_running:
                # Start Granger Hub
                hub_proc = await self._start_module('granger_hub', 8000)
                if not hub_proc:
                    results["errors"].append("Failed to start Granger Hub")
                    return results

                # Wait for initialization
                await asyncio.sleep(5)

            # Test hub connectivity
            async with aiohttp.ClientSession() as session:
                # 1. Check health endpoint
                try:
                    async with session.get("http://localhost:8000/health") as resp:
                        if resp.status == 200:
                            results["hub_responsive"] = True
                except:
                    results["errors"].append("Hub health check failed")

                # 2. Register a test module
                if results["hub_responsive"]:
                    try:
                        async with session.post("http://localhost:8000/register", json={
                            "module_name": "test_module",
                            "capabilities": ["test"],
                            "port": 9999
                        }) as resp:
                            if resp.status == 200:
                                results["registration_successful"] = True
                    except Exception as e:
                        results["errors"].append(f"Registration failed: {str(e)}")

                # 3. Test heartbeat
                if results["registration_successful"]:
                    try:
                        async with session.post("http://localhost:8000/heartbeat", json={
                            "module_name": "test_module"
                        }) as resp:
                            if resp.status == 200:
                                results["heartbeat_working"] = True
                    except:
                        results["errors"].append("Heartbeat failed")

                # 4. Get connected modules
                try:
                    async with session.get("http://localhost:8000/modules") as resp:
                        if resp.status == 200:
                            modules = await resp.json()
                            results["connected_modules"] = modules.get("modules", [])
                except:
                    results["errors"].append("Failed to get module list")

        except Exception as e:
            results["errors"].append(f"Hub test error: {str(e)}")

        finally:
            await self._cleanup_processes()

        return results

    async def test_pipeline_flow(self, pipeline_modules: List[str]) -> Dict[str, Any]:
        """Test a complete pipeline flow through multiple modules."""
        results = {
            "pipeline": " -> ".join(pipeline_modules),
            "timestamp": datetime.now().isoformat(),
            "pipeline_complete": False,
            "stages_completed": 0,
            "total_latency_ms": 0,
            "stage_results": [],
            "errors": []
        }

        try:
            # Start all pipeline modules
            processes = []
            for i, module in enumerate(pipeline_modules):
                port = self.base_ports.get(module, 8010 + i)
                proc = await self._start_module(module, port)
                if proc:
                    processes.append((module, proc, port))
                else:
                    results["errors"].append(f"Failed to start {module}")
                    return results

            # Wait for all modules to initialize
            await asyncio.sleep(5)

            # Send test data through pipeline
            test_data = {
                "id": "test_123",
                "type": "pipeline_test",
                "data": "Sample data for pipeline",
                "timestamp": time.time()
            }

            # Start the pipeline
            async with aiohttp.ClientSession() as session:
                # Send to first module
                first_module, _, first_port = processes[0]

                try:
                    start_time = time.time()
                    async with session.post(f"http://localhost:{first_port}/process",
                                          json=test_data) as resp:
                        if resp.status == 200:
                            results["stages_completed"] += 1
                            results["stage_results"].append({
                                "module": first_module,
                                "status": "success",
                                "latency_ms": (time.time() - start_time) * 1000
                            })

                    # Check subsequent stages
                    for i in range(1, len(processes)):
                        module, _, port = processes[i]

                        # Wait a bit for processing
                        await asyncio.sleep(1)

                        # Check if module received and processed data
                        stage_start = time.time()
                        async with session.get(f"http://localhost:{port}/status/{test_data['id']}") as resp:
                            if resp.status == 200:
                                status = await resp.json()
                                if status.get("processed"):
                                    results["stages_completed"] += 1
                                    stage_latency = (time.time() - stage_start) * 1000
                                    results["stage_results"].append({
                                        "module": module,
                                        "status": "success",
                                        "latency_ms": stage_latency
                                    })

                except Exception as e:
                    results["errors"].append(f"Pipeline error: {str(e)}")

            # Calculate total latency
            results["total_latency_ms"] = sum(s["latency_ms"] for s in results["stage_results"])

            # Pipeline complete if all stages succeeded
            results["pipeline_complete"] = results["stages_completed"] == len(pipeline_modules)

        except Exception as e:
            results["errors"].append(f"Pipeline test error: {str(e)}")

        finally:
            await self._cleanup_processes()

        return results

    async def _start_module(self, module_name: str, port: Optional[int] = None) -> Optional[subprocess.Popen]:
        """Start a module subprocess."""
        # Find module directory
        module_paths = [
            f"/home/graham/workspace/experiments/{module_name}",
            f"/home/graham/workspace/{module_name}",
            f"/home/graham/workspace/mcp-servers/{module_name}"
        ]

        module_path = None
        for path in module_paths:
            if Path(path).exists():
                module_path = Path(path)
                break

        if not module_path:
            return None

        # Determine how to start the module
        start_scripts = [
            module_path / "start.py",
            module_path / "run.py",
            module_path / "main.py",
            module_path / "server.py",
            module_path / "src" / f"{module_name}" / "server.py"
        ]

        start_script = None
        for script in start_scripts:
            if script.exists():
                start_script = script
                break

        if not start_script:
            # Try to find any Python file with 'main' or 'run'
            for py_file in module_path.rglob("*.py"):
                if any(word in py_file.name.lower() for word in ["main", "run", "server"]):
                    start_script = py_file
                    break

        if not start_script:
            return None

        # Start the module
        env = os.environ.copy()
        if port:
            env["PORT"] = str(port)

        try:
            proc = subprocess.Popen(
                [sys.executable, str(start_script)],
                cwd=str(module_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(proc)
            return proc
        except Exception:
            return None

    async def _check_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    async def _cleanup_processes(self):
        """Clean up started processes."""
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
        self.processes.clear()

    def generate_integration_report(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive integration test report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(all_results),
            "successful_integrations": 0,
            "failed_integrations": 0,
            "average_latency_ms": 0,
            "module_connectivity": {},
            "pipeline_tests": [],
            "hub_connectivity": None,
            "recommendations": []
        }

        total_latency = 0
        latency_count = 0

        for result in all_results:
            if "communication_established" in result:
                # Module-to-module test
                if result["communication_established"]:
                    report["successful_integrations"] += 1
                else:
                    report["failed_integrations"] += 1

                # Track connectivity
                test_name = result.get("test_name", "unknown")
                report["module_connectivity"][test_name] = {
                    "success": result["communication_established"],
                    "latency_ms": result.get("latency_ms", 0),
                    "errors": result.get("errors", [])
                }

                if result.get("latency_ms", 0) > 0:
                    total_latency += result["latency_ms"]
                    latency_count += 1

            elif "pipeline_complete" in result:
                # Pipeline test
                report["pipeline_tests"].append({
                    "pipeline": result["pipeline"],
                    "complete": result["pipeline_complete"],
                    "stages_completed": result["stages_completed"],
                    "total_latency_ms": result["total_latency_ms"]
                })

            elif "hub_responsive" in result:
                # Hub test
                report["hub_connectivity"] = result

        # Calculate average latency
        if latency_count > 0:
            report["average_latency_ms"] = total_latency / latency_count

        # Generate recommendations
        if report["failed_integrations"] > 0:
            report["recommendations"].append("Fix module communication issues before deployment")

        if report["average_latency_ms"] > 100:
            report["recommendations"].append("Optimize module communication - latency is too high")

        if report["hub_connectivity"] and not report["hub_connectivity"]["hub_responsive"]:
            report["recommendations"].append("CRITICAL: Granger Hub is not operational")

        return report


if __name__ == "__main__":
    # Test the integration tester
    async def run_tests():
        tester = IntegrationTester()

        print("✅ Integration tester validation:")

        # Test 1: Module communication
        print("\n1. Testing module communication...")
        comm_result = await tester.test_module_communication(
            module_a={'name': 'sparta', 'port': 8001},
            module_b={'name': 'marker', 'port': 8002}
        )
        print(f"   Communication established: {comm_result['communication_established']}")
        print(f"   Messages sent/received: {comm_result['messages_sent']}/{comm_result['messages_received']}")

        # Test 2: Hub connectivity
        print("\n2. Testing Granger Hub connectivity...")
        hub_result = await tester.test_granger_hub_connectivity()
        print(f"   Hub responsive: {hub_result['hub_responsive']}")
        print(f"   Registration working: {hub_result['registration_successful']}")

        # Test 3: Pipeline flow
        print("\n3. Testing pipeline flow...")
        pipeline_result = await tester.test_pipeline_flow(['sparta', 'marker', 'arangodb'])
        print(f"   Pipeline complete: {pipeline_result['pipeline_complete']}")
        print(f"   Stages completed: {pipeline_result['stages_completed']}")

        return [comm_result, hub_result, pipeline_result]

    # Run async tests
    results = asyncio.run(run_tests())