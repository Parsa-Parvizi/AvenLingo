#!/usr/bin/env python3
"""
Installation script for performance optimization tools
Handles virtual environment setup and package installation
"""
import subprocess
import sys
import os
import venv

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def create_virtual_environment():
    """Create a virtual environment if one doesn't exist"""
    venv_path = os.path.join(os.getcwd(), 'venv')
    
    if not os.path.exists(venv_path):
        print("🔧 Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        print(f"✅ Virtual environment created at: {venv_path}")
        return venv_path
    else:
        print(f"✅ Virtual environment already exists at: {venv_path}")
        return venv_path

def get_pip_command(venv_path=None):
    """Get the correct pip command for the environment"""
    if venv_path:
        if os.name == 'nt':  # Windows
            return os.path.join(venv_path, 'Scripts', 'pip')
        else:  # Unix/Linux/macOS
            return os.path.join(venv_path, 'bin', 'pip')
    else:
        return 'pip'

def install_packages(pip_cmd, packages):
    """Install packages using pip"""
    for package in packages:
        print(f"📦 Installing {package}...")
        try:
            result = subprocess.run([pip_cmd, 'install', package], 
                                 capture_output=True, text=True, check=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            print(f"Error output: {e.stderr}")

def main():
    """Main installation function"""
    print("🚀 Performance Tools Installation")
    print("=" * 40)
    
    # Essential packages (lightweight)
    essential_packages = [
        'psutil',  # For memory monitoring
    ]
    
    # Optional packages (for development)
    optional_packages = [
        'django-debug-toolbar',
        'django-extensions',
        'django-silk',
        'locust',
        'memory-profiler',
    ]
    
    # Check if we're in a virtual environment
    if check_virtual_environment():
        print("✅ Virtual environment detected")
        pip_cmd = 'pip'
        venv_path = None
    else:
        print("⚠️  No virtual environment detected")
        
        # Ask user if they want to create one
        response = input("Would you like to create a virtual environment? (y/n): ").lower()
        if response == 'y':
            venv_path = create_virtual_environment()
            pip_cmd = get_pip_command(venv_path)
            
            # Instructions for activating venv
            if os.name == 'nt':
                activate_cmd = f"{venv_path}\\Scripts\\activate"
            else:
                activate_cmd = f"source {venv_path}/bin/activate"
            
            print(f"\n📋 To activate the virtual environment, run:")
            print(f"   {activate_cmd}")
            print(f"\n🔄 Then re-run this script or install packages manually\n")
            
        else:
            print("❌ Cannot install packages in externally managed environment")
            print("💡 Solutions:")
            print("   1. Create virtual environment: python3 -m venv venv")
            print("   2. Use pipx for isolated packages: pipx install <package>")
            print("   3. Use system packages: sudo apt install python3-<package>")
            return
    
    print("\n📦 Installing essential packages...")
    install_packages(pip_cmd, essential_packages)
    
    print("\n🤔 Install optional development packages? (y/n): ", end="")
    if input().lower() == 'y':
        print("\n📦 Installing optional packages...")
        install_packages(pip_cmd, optional_packages)
    
    print("\n✅ Installation complete!")
    print("\n🔧 Next steps:")
    print("   1. Test performance: python performance_monitor.py --quick")
    print("   2. Run Django: python manage.py runserver")

if __name__ == '__main__':
    main() 