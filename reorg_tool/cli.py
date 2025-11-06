"""
Command-line interface for the reorganization system.

Provides user-friendly commands to execute reorganization operations.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .config_loader import ConfigLoader
from .orchestrator import ReorganizationOrchestrator
from .rollback import RollbackService
from .validator import ReorganizationValidator
from .reporter import ReorganizationReporter
from .models import ReorgConfig
from .exceptions import ReorgError


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.
    
    Returns:
        ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='reorg',
        description='File Reorganization Tool - Safely reorganize project files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize configuration file
  reorg init
  
  # Execute reorganization
  reorg reorganize
  
  # Execute with custom config
  reorg reorganize --config my_config.yaml
  
  # Dry run (no actual changes)
  reorg reorganize --dry-run
  
  # Rollback reorganization
  reorg rollback
  
  # Validate reorganization results
  reorg validate
  
  # Generate report
  reorg report
"""
    )
    
    # Global options
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output (errors only)'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )
    
    # Init command
    init_parser = subparsers.add_parser(
        'init',
        help='Create default configuration file'
    )
    init_parser.add_argument(
        '--output',
        default='.reorg_config.yaml',
        help='Output path for configuration file (default: .reorg_config.yaml)'
    )
    
    # Reorganize command
    reorg_parser = subparsers.add_parser(
        'reorganize',
        help='Execute file reorganization'
    )
    reorg_parser.add_argument(
        '--config',
        help='Path to configuration file'
    )
    reorg_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run (no actual changes)'
    )
    reorg_parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Disable backup creation'
    )
    reorg_parser.add_argument(
        '--project-root',
        help='Project root directory (overrides config)'
    )
    
    # Rollback command
    rollback_parser = subparsers.add_parser(
        'rollback',
        help='Rollback reorganization'
    )
    rollback_parser.add_argument(
        '--log',
        help='Path to transaction log file'
    )
    rollback_parser.add_argument(
        '--backup',
        help='Path to backup directory for verification'
    )
    rollback_parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate reorganization results'
    )
    validate_parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory'
    )
    
    # Report command
    report_parser = subparsers.add_parser(
        'report',
        help='Generate reorganization report'
    )
    report_parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory'
    )
    report_parser.add_argument(
        '--output',
        help='Output path for report'
    )
    
    return parser


def cmd_init(args) -> int:
    """
    Execute init command.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Exit code (0 for success)
    """
    try:
        output_path = ConfigLoader.create_default_config(args.output)
        print(f"✅ Created default configuration file: {output_path}")
        print(f"\nEdit the configuration file and then run:")
        print(f"  reorg reorganize --config {output_path}")
        return 0
    
    except ReorgError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def cmd_reorganize(args) -> int:
    """
    Execute reorganize command.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Exit code (0 for success)
    """
    try:
        # Load configuration
        if args.config:
            config = ConfigLoader.load_config(args.config)
        else:
            config = ConfigLoader.load_config()
        
        # Apply command-line overrides
        if args.dry_run:
            config.dry_run = True
        if args.no_backup:
            config.backup_enabled = False
        if args.project_root:
            config.project_root = args.project_root
        
        # Confirm with user
        if not config.dry_run:
            print("⚠️  WARNING: This will reorganize your project files.")
            print(f"Project root: {config.project_root}")
            print(f"Backup enabled: {config.backup_enabled}")
            
            response = input("\nContinue? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cancelled.")
                return 0
        
        # Execute reorganization
        print("\n" + "="*60)
        print("Starting File Reorganization")
        print("="*60 + "\n")
        
        orchestrator = ReorganizationOrchestrator(config)
        result = orchestrator.execute_reorganization()
        
        # Print summary
        print("\n" + "="*60)
        if result.success:
            print("✅ Reorganization completed successfully!")
        else:
            print("❌ Reorganization failed or completed with errors")
        print("="*60)
        
        print(f"\nDuration: {result.duration:.2f} seconds")
        print(f"Files moved: {result.files_moved}")
        print(f"Links created: {result.links_created}")
        print(f"Files deleted: {result.files_deleted}")
        
        if result.errors:
            print(f"\n⚠️  Errors: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more")
        
        if result.backup_path:
            print(f"\n💾 Backup: {result.backup_path}")
        
        print(f"\n📄 Report: REORGANIZATION_SUMMARY.md")
        
        return 0 if result.success else 1
    
    except ReorgError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_rollback(args) -> int:
    """
    Execute rollback command.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Exit code (0 for success)
    """
    try:
        project_root = Path(args.project_root).resolve()
        
        # Find transaction log
        if args.log:
            log_path = args.log
        else:
            log_path = project_root / ".reorg_transaction_log.json"
            if not Path(log_path).exists():
                print(f"❌ Transaction log not found: {log_path}", file=sys.stderr)
                print("Specify log path with --log option", file=sys.stderr)
                return 1
        
        # Confirm with user
        print("⚠️  WARNING: This will rollback the reorganization.")
        print(f"Transaction log: {log_path}")
        
        response = input("\nContinue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            return 0
        
        # Execute rollback
        print("\nExecuting rollback...")
        
        rollback_service = RollbackService(str(project_root))
        result = rollback_service.execute_rollback(
            str(log_path),
            backup_path=args.backup
        )
        
        # Print summary
        print("\n" + "="*60)
        if result['success']:
            print("✅ Rollback completed successfully!")
        else:
            print("❌ Rollback failed or completed with errors")
        print("="*60)
        
        print(f"\nTotal operations: {result['total_operations']}")
        print(f"Reversed: {result['reversed']}")
        print(f"Failed: {result['failed']}")
        
        if result['errors']:
            print(f"\n⚠️  Errors:")
            for error in result['errors'][:5]:
                print(f"  - {error}")
        
        return 0 if result['success'] else 1
    
    except ReorgError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_validate(args) -> int:
    """
    Execute validate command.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Exit code (0 for success)
    """
    try:
        project_root = args.project_root
        
        print("Validating reorganization results...")
        
        validator = ReorganizationValidator(project_root)
        validator.validate_all()
        
        # Generate report
        report = validator.generate_validation_report()
        print("\n" + report)
        
        if validator.validation_checks.all_passed:
            print("\n✅ All validation checks passed!")
            return 0
        else:
            print("\n❌ Some validation checks failed")
            return 1
    
    except ReorgError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_report(args) -> int:
    """
    Execute report command.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Exit code (0 for success)
    """
    try:
        project_root = args.project_root
        
        print("Generating reorganization report...")
        
        reporter = ReorganizationReporter(project_root)
        
        # Generate directory tree
        tree = reporter.generate_directory_tree(max_depth=3, show_files=False)
        
        print("\n" + "="*60)
        print("Directory Structure")
        print("="*60)
        print(tree)
        
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(tree)
            print(f"\n✅ Report saved to: {output_path}")
        
        return 0
    
    except ReorgError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
    
    Returns:
        Exit code (0 for success)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Handle no command
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    if args.command == 'init':
        return cmd_init(args)
    elif args.command == 'reorganize':
        return cmd_reorganize(args)
    elif args.command == 'rollback':
        return cmd_rollback(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'report':
        return cmd_report(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
