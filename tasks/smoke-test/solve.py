"""Local echo reference program; no Agent or PDE solver."""
import argparse
from caeoj.sdk import load_problem, write_result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    problem = load_problem(args.input)
    if problem.manifest.get("task") != "smoke-test":
        raise ValueError("This program implements smoke-test only.")
    write_result(args.output, problem, {spec["array"]: problem.arrays[spec["array"]].copy()
                                      for spec in problem.manifest["outputs"].values()})


if __name__ == "__main__":
    main()
