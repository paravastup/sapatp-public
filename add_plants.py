#!/usr/bin/env python3
"""
Script to add Plant objects and associate them with a user.
Run this script inside the Docker container using:
docker-compose exec web python add_plants.py
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')
django.setup()

from django.contrib.auth.models import User
from stockcheck.models import Plant

def add_plants_to_user(username):
    """Add plant objects and associate them with the specified user."""
    try:
        user = User.objects.get(username=username)
        print(f"Found user: {user.username}")
        
        # Create plant objects if they don't exist
        plants_data = [
            {'code': '1001', 'description': 'ACME Corp'},
            {'code': '1002', 'description': 'ACME Plant 2'},
            {'code': '1003', 'description': 'ACME Canada'},
            {'code': '1000', 'description': 'ACME Glass Plant'},
        ]
        
        for plant_data in plants_data:
            plant, created = Plant.objects.get_or_create(
                code=plant_data['code'],
                defaults={'description': plant_data['description']}
            )
            
            if created:
                print(f"Created plant: {plant.description}")
            else:
                print(f"Plant already exists: {plant.description}")
            
            # Associate plant with user
            if not plant.users.filter(id=user.id).exists():
                plant.users.add(user)
                print(f"Associated plant {plant.description} with user {user.username}")
            else:
                print(f"Plant {plant.description} already associated with user {user.username}")
        
        print("\nPlants associated with user:")
        for plant in user.plant.all():
            print(f"- {plant.code}: {plant.description}")
            
        return True
    except User.DoesNotExist:
        print(f"User {username} not found")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    username = input("Enter the username to associate plants with: ")
    add_plants_to_user(username)