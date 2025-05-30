📋 Validation Summary:")
    click.echo(f"   Model: {validation_results['model']}")
    
    click.echo("\n   Categories:")
    for category, count in summary['categories'].items():
        emoji = "✅" if category == "good" else "⚠️"
        click.echo(f"     {emoji} {category}: {count}")
    
    click.echo("\n   Severities:")
    for severity, count in summary['severities'].items():
        click.echo(f"     - {severity}: {count}")
    
    click.echo(f"\n   Total Issues Found: {summary['total_issues']}")
    
    # Show problematic tests
    if summary['problematic_tests']:
        click.echo("\n⚠️  Problematic Tests:")
        for test in summary['problematic_tests']:
            click.echo(f"     - {test}")
            
            if verbose:
                validation = validation_results['validations'][test]
                click.echo(f"       Category: {validation['category']}")
                click.echo(f"       Issues: {, \.join(validation['issues'])}")
    
    # Save results
    output_path = Path(output)
    with open(output_path, 'w') as f:
        json.dump({
            "test_results": test_results,
            "validation": validation_results
        }, f, indent=2)
    
    click.echo(f"\n💾 Validation results saved to: {output_path}")
    
    # Check fail conditions
    failed_categories = set(fail_on_category)
    found_categories = set(summary['categories'].keys())
    bad_categories = failed_categories.intersection(found_categories)
    
    if bad_categories:
        click.echo(f"\n❌ Found tests in prohibited categories: {bad_categories}")
        sys.exit(1)
    
    # Check confidence
    low_confidence_tests = [
        name for name, val in validation_results['validations'].items()
        if val.get('confidence', 1.0) < min_confidence
    ]
    
    if low_confidence_tests:
        click.echo(f"\n⚠️  {len(low_confidence_tests)} tests below confidence threshold")
        if verbose:
            for test in low_confidence_tests[:5]:
                click.echo(f"     - {test}")
    
    click.echo("\n✅ Validation complete!")
    return 0


if __name__ == "__main__":
    validate()
