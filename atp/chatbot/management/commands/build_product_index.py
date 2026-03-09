"""
Django management command to build FAISS product index for RAG
Usage: python manage.py build_product_index
"""
from django.core.management.base import BaseCommand
from chatbot.services.rag_indexer import ProductIndexer


class Command(BaseCommand):
    help = 'Build FAISS index for product catalog RAG'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting product index build...'))

        indexer = ProductIndexer()
        index, mapping = indexer.build_index()

        if index is not None:
            self.stdout.write(self.style.SUCCESS(
                f'[SUCCESS] Index built successfully! {len(mapping)} products indexed.'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                '[ERROR] Index build failed! Check logs for details.'
            ))
