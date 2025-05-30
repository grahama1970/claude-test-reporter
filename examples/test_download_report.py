📄 Report Preview:")
            print("=" * 80)
            for line in lines[:50]:
                print(line.rstrip())
            if len(lines) > 50:
                print(f"\n... ({len(lines) - 50} more lines)")
    else:
        print("❌ Report generation failed")

if __name__ == "__main__":
    test_report_generation()