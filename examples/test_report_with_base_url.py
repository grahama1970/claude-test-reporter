✅ Report generated successfully!")
    print(f"📊 View your report at: {report_url}")
    print(f"\n💡 Note: Make sure your web server is running at {generator.base_url}")
    print(f"   If using Python's SimpleHTTPServer:")
    print(f"   cd {Path.cwd()}")
    print(f"   python -m http.server 8 --bind 192.168.86.49")

if __name__ == "__main__":
    main()