"""Management command to run the evaluation suite."""

import json
import logging
import time

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Run the CodeMentor AI evaluation suite."""

    help = "Run evaluation metrics on the multi-agent pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="evaluation_results.json",
            help="Output file for evaluation results (default: evaluation_results.json)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed results for each test case",
        )
        parser.add_argument(
            "--category",
            type=str,
            default="all",
            choices=["all", "debug", "explain", "generate"],
            help="Category of test cases to evaluate (default: all)",
        )

    def handle(self, *args, **options):
        from evaluation.metrics import run_full_evaluation

        output_file = options["output"]
        verbose = options["verbose"]
        category = options["category"]

        self.stdout.write(self.style.NOTICE(f"Running evaluation suite (category: {category})..."))
        start_time = time.time()

        try:
            results = run_full_evaluation(category=category, verbose=verbose)

            elapsed = time.time() - start_time

            # Display summary
            self.stdout.write(self.style.SUCCESS(f"\nEvaluation complete in {elapsed:.2f}s"))
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"  Overall Score:          {results['overall_score']:.2%}")
            self.stdout.write(f"  Hallucination Rate:     {results['hallucination_rate']:.2%}")
            self.stdout.write(f"  Retrieval Precision:    {results['retrieval_precision']:.2%}")
            self.stdout.write(f"  Code Fix Accuracy:      {results['code_fix_accuracy']:.2%}")
            self.stdout.write(f"  Total Test Cases:       {results['total_cases']}")
            self.stdout.write(f"  Passed:                 {results['passed']}")
            self.stdout.write(f"  Failed:                 {results['failed']}")
            self.stdout.write(f"{'='*60}\n")

            # Save to file
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            self.stdout.write(self.style.SUCCESS(f"Results saved to {output_file}"))

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            raise CommandError(f"Evaluation failed: {e}")
