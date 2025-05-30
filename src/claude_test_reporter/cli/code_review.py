✅ Comparison complete!")
            click.echo(f"📊 Comparison saved to: {result['comparison_path']}")
            
            # Show summary
            if verbose:
                click.echo("\nReview Summary:")
                for model_name, review_result in result["reviews"].items():
                    status = "✅" if review_result["success"] else "❌"
                    click.echo(f"  {status} {model_name}")
        else:
            click.echo(f"❌ {result['message']}")
            sys.exit(1)
            
    else:
        # Single model review
        result = reviewer.review_repository(
            repo_path=repo,
            custom_prompt=custom_prompt,
            temperature=temperature,
            output_path=output
        )
        
        if result["success"]:
            if output:
                click.echo(f"\n✅ Review complete!")
            else:
                # Print to stdout if no output file specified
                click.echo("\n" + "="*60 + "\n")
                click.echo(result["report"]["review"])
                click.echo("\n" + "="*60)
                
            # Show statistics if verbose
            if verbose and "statistics" in result["report"]:
                stats = result["report"]["statistics"]
                click.echo(f"\n📊 Change Statistics:")
                click.echo(f"  Total Files: {stats['total_files']}")
                click.echo(f"  Total Changes: {stats['total_changes']}")
                click.echo(f"  Staged: {stats['staged']['files']} files")
                click.echo(f"  Untracked: {stats['untracked_files']} files")
                
        else:
            click.echo(f"❌ {result['message']}")
            sys.exit(1)


if __name__ == "__main__":
    code_review()
