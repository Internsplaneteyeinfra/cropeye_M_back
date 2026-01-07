from django.core.management.base import BaseCommand
from django.conf import settings
import psutil
import os
import json
from datetime import datetime
from pathlib import Path

class Command(BaseCommand):
    help = 'Monitor system resources (RAM, storage, Django-specific usage)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format',
        )
        parser.add_argument(
            '--save',
            type=str,
            help='Save metrics to specified file',
        )

    def handle(self, *args, **options):
        metrics = self.get_system_metrics()
        
        if options['json']:
            output = json.dumps(metrics, indent=2)
        else:
            output = self.format_metrics(metrics)
        
        if options['save']:
            with open(options['save'], 'w') as f:
                json.dump(metrics, f, indent=2)
            self.stdout.write(f"Metrics saved to {options['save']}")
        
        self.stdout.write(output)

    def get_system_metrics(self):
        """Get comprehensive system metrics"""
        
        # RAM Usage
        memory = psutil.virtual_memory()
        ram_metrics = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'percent_used': memory.percent,
            'free_gb': round(memory.free / (1024**3), 2)
        }
        
        # Storage Usage
        disk = psutil.disk_usage('/')
        storage_metrics = {
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'percent_used': round((disk.used / disk.total) * 100, 2)
        }
        
        # Django-specific directories
        django_dirs = self.analyze_django_directories()
        
        # Process metrics
        process_metrics = self.get_process_metrics()
        
        # Database size (if available)
        db_metrics = self.get_database_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'ram': ram_metrics,
            'storage': storage_metrics,
            'django_directories': django_dirs,
            'process': process_metrics,
            'database': db_metrics
        }

    def analyze_django_directories(self):
        """Analyze Django-specific directory sizes"""
        django_dirs = {}
        django_paths = [
            'media', 'staticfiles', '__pycache__', 'migrations',
            'templates', 'static', 'envm', 'model'
        ]
        
        for path in django_paths:
            if os.path.exists(path):
                try:
                    total_size = 0
                    file_count = 0
                    dir_count = 0
                    
                    for root, dirs, files in os.walk(path):
                        dir_count += len(dirs)
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                total_size += os.path.getsize(file_path)
                                file_count += 1
                            except:
                                pass
                    
                    django_dirs[path] = {
                        'size_mb': round(total_size / (1024**2), 2),
                        'size_gb': round(total_size / (1024**3), 2),
                        'file_count': file_count,
                        'directory_count': dir_count
                    }
                    
                except Exception as e:
                    django_dirs[path] = {'error': str(e)}
        
        return django_dirs

    def get_process_metrics(self):
        """Get current Django process metrics"""
        try:
            current_process = psutil.Process()
            return {
                'memory_mb': round(current_process.memory_info().rss / (1024**2), 2),
                'cpu_percent': current_process.cpu_percent(),
                'num_threads': current_process.num_threads(),
                'create_time': datetime.fromtimestamp(current_process.create_time()).isoformat()
            }
        except:
            return {'error': 'Could not get process metrics'}

    def get_database_metrics(self):
        """Get database size metrics"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as size,
                        pg_database_size(current_database()) as size_bytes
                """)
                result = cursor.fetchone()
                if result:
                    return {
                        'size': result[0],
                        'size_bytes': result[1],
                        'size_mb': round(result[1] / (1024**2), 2)
                    }
        except:
            pass
        
        return {'error': 'Could not get database metrics'}

    def format_metrics(self, metrics):
        """Format metrics for human-readable output"""
        output = []
        output.append("=== System Resource Monitor ===")
        output.append(f"Timestamp: {metrics['timestamp']}")
        
        # RAM
        output.append("\n--- RAM Usage ---")
        ram = metrics['ram']
        output.append(f"Total: {ram['total_gb']} GB")
        output.append(f"Used: {ram['used_gb']} GB ({ram['percent_used']}%)")
        output.append(f"Available: {ram['available_gb']} GB")
        output.append(f"Free: {ram['free_gb']} GB")
        
        # Storage
        output.append("\n--- Storage Usage ---")
        storage = metrics['storage']
        output.append(f"Total: {storage['total_gb']} GB")
        output.append(f"Used: {storage['used_gb']} GB ({storage['percent_used']}%)")
        output.append(f"Free: {storage['free_gb']} GB")
        
        # Django directories
        output.append("\n--- Django Directory Sizes ---")
        for dir_name, dir_info in metrics['django_directories'].items():
            if 'error' not in dir_info:
                output.append(f"{dir_name}: {dir_info['size_mb']} MB ({dir_info['file_count']} files)")
            else:
                output.append(f"{dir_name}: Error - {dir_info['error']}")
        
        # Process
        output.append("\n--- Process Metrics ---")
        process = metrics['process']
        if 'error' not in process:
            output.append(f"Memory: {process['memory_mb']} MB")
            output.append(f"CPU: {process['cpu_percent']}%")
            output.append(f"Threads: {process['num_threads']}")
        else:
            output.append(f"Process: Error - {process['error']}")
        
        # Database
        output.append("\n--- Database ---")
        db = metrics['database']
        if 'error' not in db:
            output.append(f"Size: {db['size']} ({db['size_mb']} MB)")
        else:
            output.append(f"Database: Error - {db['error']}")
        
        return "\n".join(output)
