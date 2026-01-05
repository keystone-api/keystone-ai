"""
MachineNativeOps Auto-Monitor - Main Entry Point

Usage:
    python -m machinenativenops_auto_monitor [options]
    
Options:
    --config PATH       Configuration file path (default: /etc/machinenativeops/auto-monitor.yaml)
    --verbose           Enable verbose logging
    --dry-run           Run without actually sending alerts or storing data
    --daemon            Run as daemon process
    
Examples:
    python -m machinenativenops_auto_monitor --config config.yaml
    python -m machinenativenops_auto_monitor --daemon --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

from .app import AutoMonitorApp
from .config import AutoMonitorConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the auto-monitor application."""
    parser = argparse.ArgumentParser(
        description="MachineNativeOps Auto-Monitor - 自動監控系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default configuration
  python -m machinenativenops_auto_monitor
  
  # Start with custom config file
  python -m machinenativenops_auto_monitor --config /path/to/config.yaml
  
  # Start with verbose logging
  python -m machinenativenops_auto_monitor --verbose
  
  # Run in dry-run mode
  python -m machinenativenops_auto_monitor --dry-run
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='/etc/machinenativeops/auto-monitor.yaml',
        help='Configuration file path (YAML)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without actually sending alerts or storing data'
    )
    parser.add_argument(
        '--daemon',
        '-d',
        action='store_true',
        help='Run as daemon process'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}, using defaults")
            config = AutoMonitorConfig()
        else:
            logger.info(f"Loading configuration from: {config_path}")
            config = AutoMonitorConfig.from_file(config_path)
        
        # Override with command-line options
        if args.dry_run:
            config.dry_run = True
            logger.info("Running in DRY-RUN mode")
        
        if args.verbose:
            config.log_level = "DEBUG"
        
        # Create and start application
        app = AutoMonitorApp(config)
        
        logger.info("Starting MachineNativeOps Auto-Monitor...")
        logger.info(f"Version: {config.version}")
        logger.info(f"Namespace: {config.namespace}")
        
        if args.daemon:
            logger.info("Running in daemon mode")
            app.run_daemon()
        else:
            logger.info("Running in foreground mode")
            app.run()
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
