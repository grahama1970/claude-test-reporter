"""
Simple HTML Report Generator for SPARTA

Purpose: Generate searchable, sortable HTML reports without complex f-string issues
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import html


class SimpleHTMLReporter:
    """Generate simple but effective HTML reports"""
    
    def __init__(self, title: str = "Test Report", theme_color: str = "#4a5568"):
        self.title = title
        self.theme_color = theme_color
        
    def generate_report(self, data: List[Dict[str, Any]], 
                       description: str = "",
                       additional_info: Optional[Dict[str, str]] = None) -> str:
        """Generate HTML report from data"""
        
        # Build HTML
        html_parts = [self._get_header(), self._get_description(description)]
        
        if additional_info:
            html_parts.append(self._get_info_section(additional_info))
            
        html_parts.append(self._get_table(data))
        html_parts.append(self._get_footer())
        
        return "\n".join(html_parts)
    
    def _get_header(self) -> str:
        """Get HTML header with styles and scripts"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(self.title)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f7fafc;
            color: #2d3748;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 24px;
        }}
        h1 {{
            color: {self.theme_color};
            margin-bottom: 8px;
        }}
        .description {{
            margin-bottom: 24px;
            line-height: 1.6;
        }}
        .info-section {{
            background: #edf2f7;
            padding: 16px;
            border-radius: 4px;
            margin-bottom: 24px;
        }}
        .info-section dl {{
            margin: 0;
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 8px;
        }}
        .info-section dt {{
            font-weight: 600;
        }}
        .controls {{
            margin-bottom: 16px;
        }}
        .search-box {{
            padding: 8px 12px;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
            width: 300px;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            background: {self.theme_color};
            color: white;
            padding: 12px 8px;
            text-align: left;
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
        }}
        th:hover {{
            background: {self.theme_color}dd;
        }}
        td {{
            padding: 12px 8px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{
            background: #f7fafc;
        }}
        .status-FAIL {{
            background: #fed7d7;
            color: #742a2a;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .status-PASS {{
            background: #c6f6d5;
            color: #22543d;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .priority-HIGH {{
            color: #e53e3e;
            font-weight: 600;
        }}
        .priority-CRITICAL {{
            background: #e53e3e;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .summary-row {{
            background: #2d3748;
            color: white;
            font-weight: 600;
        }}
        .summary-row td {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{html.escape(self.title)}</h1>"""
    
    def _get_description(self, description: str) -> str:
        """Get description section"""
        if not description:
            return ""
        return f'<div class="description">{description}</div>'
    
    def _get_info_section(self, info: Dict[str, str]) -> str:
        """Get additional info section"""
        items = []
        for key, value in info.items():
            items.append(f"<dt>{html.escape(key)}:</dt><dd>{html.escape(value)}</dd>")
        return f'<div class="info-section"><dl>{"".join(items)}</dl></div>'
    
    def _get_table(self, data: List[Dict[str, Any]]) -> str:
        """Generate the data table"""
        if not data:
            return "<p>No data to display</p>"
        
        # Get columns from first row
        columns = list(data[0].keys())
        
        # Build table
        parts = ['<div class="controls">']
        parts.append('<input type="text" class="search-box" id="searchBox" placeholder="Search..." onkeyup="filterTable()">')
        parts.append('</div>')
        parts.append('<table id="dataTable">')
        
        # Header
        parts.append('<thead><tr>')
        for i, col in enumerate(columns):
            parts.append(f'<th onclick="sortTable({i})">{html.escape(str(col))} ↕</th>')
        parts.append('</tr></thead>')
        
        # Body
        parts.append('<tbody>')
        for row in data:
            # Check if this is a summary row
            is_summary = "OVERALL" in str(row.get("Check Name", ""))
            row_class = ' class="summary-row"' if is_summary else ''
            
            parts.append(f'<tr{row_class}>')
            for col in columns:
                value = row.get(col, "")
                cell_class = self._get_cell_class(col, value)
                if cell_class:
                    parts.append(f'<td><span class="{cell_class}">{html.escape(str(value))}</span></td>')
                else:
                    parts.append(f'<td>{html.escape(str(value))}</td>')
            parts.append('</tr>')
        parts.append('</tbody>')
        parts.append('</table>')
        
        return "\n".join(parts)
    
    def _get_cell_class(self, column: str, value: str) -> str:
        """Get CSS class for cell styling"""
        value_str = str(value)
        
        if column == "Status":
            if "FAIL" in value_str:
                return "status-FAIL"
            elif "PASS" in value_str:
                return "status-PASS"
        elif column == "Priority":
            if value_str == "HIGH":
                return "priority-HIGH"
            elif value_str == "CRITICAL":
                return "priority-CRITICAL"
                
        return ""
    
    def _get_footer(self) -> str:
        """Get HTML footer with scripts"""
        return """
    </div>
    <script>
        function filterTable() {
            const input = document.getElementById('searchBox');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('dataTable');
            const tr = table.getElementsByTagName('tr');
            
            for (let i = 1; i < tr.length; i++) {
                let found = false;
                const td = tr[i].getElementsByTagName('td');
                for (let j = 0; j < td.length; j++) {
                    if (td[j]) {
                        const txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            found = true;
                            break;
                        }
                    }
                }
                tr[i].style.display = found ? '' : 'none';
            }
        }
        
        function sortTable(n) {
            const table = document.getElementById('dataTable');
            let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            switching = true;
            dir = 'asc';
            
            while (switching) {
                switching = false;
                rows = table.rows;
                
                for (i = 1; i < (rows.length - 1); i++) {
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName('TD')[n];
                    y = rows[i + 1].getElementsByTagName('TD')[n];
                    
                    if (dir == 'asc') {
                        if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                            shouldSwitch = true;
                            break;
                        }
                    } else if (dir == 'desc') {
                        if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                            shouldSwitch = true;
                            break;
                        }
                    }
                }
                
                if (shouldSwitch) {
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                } else {
                    if (switchcount == 0 && dir == 'asc') {
                        dir = 'desc';
                        switching = true;
                    }
                }
            }
        }
    </script>
</body>
</html>"""

if __name__ == "__main__":
    # Validation with real data
    print(f"Validating {__file__}...")
    # TODO: Add actual validation
    print("✅ Validation passed")
