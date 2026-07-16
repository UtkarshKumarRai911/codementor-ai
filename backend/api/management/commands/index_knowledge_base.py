"""Management command to index the knowledge base into ChromaDB."""

import logging
import time

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Index knowledge base documents into the ChromaDB vector store."""

    help = "Index knowledge base editorials and documents into ChromaDB for RAG retrieval"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default="sample",
            choices=["sample", "scraped", "all"],
            help="Source of documents to index (default: sample)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-indexing even if documents already exist",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Batch size for indexing (default: 50)",
        )

    def handle(self, *args, **options):
        from knowledge_base.indexer import KnowledgeBaseIndexer

        source = options["source"]
        force = options["force"]
        batch_size = options["batch_size"]

        self.stdout.write(self.style.NOTICE(f"Starting knowledge base indexing (source: {source})..."))
        start_time = time.time()

        try:
            indexer = KnowledgeBaseIndexer()
            stats = indexer.run(source=source, force=force, batch_size=batch_size)

            elapsed = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f"Indexing complete in {elapsed:.2f}s\n"
                    f"  Documents processed: {stats['documents_processed']}\n"
                    f"  Chunks created: {stats['chunks_created']}\n"
                    f"  Chunks indexed: {stats['chunks_indexed']}\n"
                    f"  Errors: {stats['errors']}"
                )
            )
        except Exception as e:
            logger.error(f"Knowledge base indexing failed: {e}", exc_info=True)
            raise CommandError(f"Indexing failed: {e}")
