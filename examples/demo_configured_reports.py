")
    
    # Generate reports
    sparta_url = generate_sparta_report()
    print(f"✅ SPARTA Report: {sparta_url}")
    
    marker_url = generate_marker_report()
    print(f"✅ Marker Report: {marker_url}")
    
    arango_url = generate_arangodb_report()
    print(f"✅ ArangoDB Report: {arango_url}")
    
    print(f"\n📊 All reports generated with base URL: http://192.168.86.49:8")
    print(f"💡 Make sure your web server is running at that address")


if __name__ == "__main__":
    main()