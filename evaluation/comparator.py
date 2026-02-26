from core.project import ComparisonResult


class ResultComparator:
    def compare(
        self,
        recovered: set[str],
        ground_truth: set[str],
    ) -> ComparisonResult:
        tp = recovered & ground_truth
        fp = recovered - ground_truth
        fn = ground_truth - recovered

        print("True Positives:", tp)
        print("False Positives:", fp)
        print("False Negatives:", fn)
    

        precision = len(tp) / (len(tp) + len(fp)) if tp or fp else 0.0
        recall = len(tp) / (len(tp) + len(fn)) if tp or fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        return ComparisonResult(precision, recall, f1, tp, fp, fn)
