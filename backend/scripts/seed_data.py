#!/usr/bin/env python
"""Seed script to create test user and index the knowledge base."""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codementor.settings")

import django

django.setup()

from django.contrib.auth.models import User

from knowledge_base.indexer import KnowledgeBaseIndexer


def create_test_user():
    """Create a test user for development."""
    username = "testuser"
    email = "test@codementor.ai"
    password = "testpassword123"

    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists.")
        return

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    print(f"Created test user: {username} (email: {email})")
    return user


def index_knowledge_base():
    """Index sample editorials into ChromaDB."""
    print("Indexing knowledge base...")
    indexer = KnowledgeBaseIndexer()
    stats = indexer.run(source="sample", force=False)
    print(f"Indexing complete: {stats}")


def main():
    """Run all seed operations."""
    print("=" * 50)
    print("  CodeMentor AI - Data Seeding")
    print("=" * 50)

    print("\n[1/2] Creating test user...")
    create_test_user()

    print("\n[2/2] Indexing knowledge base...")
    index_knowledge_base()

    print("\nSeeding complete!")
    print("Test credentials:")
    print("  Username: testuser")
    print("  Password: testpassword123")


if __name__ == "__main__":
    main()
