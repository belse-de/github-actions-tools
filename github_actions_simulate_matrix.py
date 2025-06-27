#!usr/bin/env python3
import copy
import itertools
import unittest


def check_var_is_list_of_dicts(var, name):
    if not isinstance(var, list):
        raise ValueError(f" Argument {name} must be a list of dictionaries.")
    if not all(isinstance(entry, dict) for entry in var):
        raise ValueError("Each entry in argument {name} must be a dictionary.")


def matrix_conf_to_matrix_inc_exc(matrix_conf: dict) -> (dict, list[dict], list[dict]):
    matrix = {k: v for k, v in matrix_conf.items() if k not in ["include", "exclude"]}
    includes = matrix_conf.get("include", [])
    excludes = matrix_conf.get("exclude", [])
    return matrix, includes, excludes


def matrix_inc_exc_to_matrix_conf(matrix: dict, include: list[dict], exclude: list[dict]) -> dict:
    matrix_conf = copy.copy(matrix)
    if include:
        matrix_conf['include'] = include
    if exclude:
        matrix_conf['exclude'] = exclude
    return matrix_conf


def matrix_to_jobs(matrix: dict) -> list[dict]:
    """
    Convert a GitHub Actions matrix configuration to a list of job configurations.

    Args:
        matrix (dict): The matrix configuration as a dictionary.

    Returns:
        list[dict]: A list of job configurations derived from the matrix.
    """
    if not isinstance(matrix, dict):
        raise ValueError("Matrix must be a dictionary.")
    if "include" in matrix:
        raise ValueError("Matrix cannot contain 'include' at this stage. Use a different function to handle includes.")
    if "exclude" in matrix:
        raise ValueError("Matrix cannot contain 'exclude' at this stage. Use a different function to handle excludes.")

    product_tasks = []
    for key, value in matrix.items():
        tasks = []
        if isinstance(value, list):
            tasks = [(key, item) for item in value]
        else:
            tasks = [(key, value)]
        product_tasks.append(tasks)

    job_list = [dict(job_fields) for job_fields in itertools.product(*product_tasks) if job_fields]
    return job_list


def include_jobs(job_list: list[dict], includes: list[dict]) -> list[dict]:
    check_var_is_list_of_dicts(job_list, 'job_list')
    check_var_is_list_of_dicts(includes, 'includes')

    # If you don't specify any matrix variables, all configurations under include will run.
    if not job_list:
        return includes

    # for all original matrix combinations get the keys
    original_keys = set(key for job in job_list for key in job.keys())

    # includes that cannot be added to any original matrix combination without overwriting a value,
    #   is added as an additional matrix combination.
    #   It does not add to the original matrix combination
    #   because that combination was not one of the original matrix combinations.
    includes_that_would_override = [include for include in includes if original_keys.issuperset(include.keys())]

    includes_add_expand = [include for include in includes if include not in includes_that_would_override]
    new_job_list = copy.deepcopy(job_list)
    for orig_job, job in zip(job_list, new_job_list):
        # for each include entry, check if it can be added to the original matrix combinations
        for include in includes_add_expand:
            include_keys = set(include.keys())

            if include_keys.isdisjoint(orig_job.keys()):
                job.update(include)
                continue

            # adds missing fields only to the original matrix combinations that include matching fields.
            common_keys = include_keys.intersection(orig_job.keys())
            common_job_fields = {k:v for k,v in orig_job.items() if k in common_keys}
            common_inc_fields = {k:v for k,v in include.items() if k in common_keys}
            if common_job_fields == common_inc_fields:
                job.update(include)
                continue

    new_job_list.extend(includes_that_would_override)

    return new_job_list


def exclude_jobs(job_list: list[dict], excludes: list[dict]) -> list[dict]:
    check_var_is_list_of_dicts(job_list, 'job_list')
    check_var_is_list_of_dicts(excludes, 'excludes')

    if not excludes:
        return job_list

    def is_not_matching_dict(dict_to_match: dict):
        def func(dic):
            dic_to_compare = {k: v for k, v in dic.items() if k in dict_to_match}
            return dic_to_compare != dict_to_match
        return func

    new_job_list = job_list
    for exclude in excludes:
        new_job_list = list(filter(is_not_matching_dict(exclude), new_job_list))

    return new_job_list


def simulate_github_actions_matrix(matrix: dict, includes: list[dict] = None, excludes: list[dict] = None) -> list[dict]:
    """
    Simulate the GitHub Actions matrix by applying includes and excludes to the job list.

    Args:
        matrix (dict): The matrix configuration as a dictionary.
        includes (list[dict], optional): List of include configurations.
        excludes (list[dict], optional): List of exclude configurations.

    Returns:
        list[dict]: A list of job configurations after applying includes and excludes.
    """
    job_list = matrix_to_jobs(matrix)
    job_list_inc = include_jobs(job_list, includes)
    job_list_exc = exclude_jobs(job_list_inc, excludes)
    return job_list_exc


def matrix_conf_to_jobs(matrix_conf: dict) -> list[dict]:
    if not isinstance(matrix_conf, dict):
        raise ValueError("Matrix config must be a dictionary.")

    includes = matrix_conf.get("include", [])
    excludes = matrix_conf.get("exclude", [])
    matrix = {k: v for k, v in matrix_conf.items() if k not in ["include", "exclude"]}
    return simulate_github_actions_matrix(matrix, includes, excludes)


def print_list_diff(expected: list, actual: list):
    if actual != expected:
        print(f"Expected {expected},\n but got {actual}")
        diff_missing = list(filter(lambda item: item not in actual, expected))
        for missing in diff_missing:
            print(f" - {missing}")

        diff_added = list(filter(lambda item: item not in expected, actual))
        for added in diff_added:
            print(f" + {added}")


class GitHubActionsSimulateMatrixTest(unittest.TestCase):

    def check_test_cases(self, test_cases):
        for name, matrix_conf, expected_jobs in test_cases:
            with self.subTest(name):
                jobs = matrix_conf_to_jobs(matrix_conf)
                print_list_diff(expected_jobs, jobs)
                self.assertEqual(expected_jobs, jobs)

    def test_matrix_conf_to_jobs(self):
        test_cases = [
            (
                "Example: Using a single-dimension matrix",
                {
                    "version": [10, 12, 14],
                },
                [
                    {"version": 10},
                    {"version": 12},
                    {"version": 14},
                ]
            ),
            (
                "two dimensional matrix",
                {
                    "version": [10, 12, 14],
                    "os": ["ubuntu-latest", "windows-latest"]
                },
                [
                    {"version": 10, "os": "ubuntu-latest"},
                    {"version": 10, "os": "windows-latest"},
                    {"version": 12, "os": "ubuntu-latest"},
                    {"version": 12, "os": "windows-latest"},
                    {"version": 14, "os": "ubuntu-latest"},
                    {"version": 14, "os": "windows-latest"},
                ]
            ),
            (
                "Example: Using a multi-dimension matrix: array of objects",
                {
                    "os": ["ubuntu-latest", "macos-latest"],
                    "node": [
                        {"version": 14},
                        {"version": 20, "env": "NODE_OPTIONS=--openssl-legacy-provider"}
                    ],
                },
                [
                    {"os": "ubuntu-latest", "node": {"version": 14}},
                    {"os": "ubuntu-latest", "node": {"version": 20, "env": "NODE_OPTIONS=--openssl-legacy-provider"}},
                    {"os": "macos-latest", "node": {"version": 14}},
                    {"os": "macos-latest", "node": {"version": 20, "env": "NODE_OPTIONS=--openssl-legacy-provider"}},
                ]
            ),
        ]
        self.check_test_cases(test_cases)

    def test_matrix_conf_include(self):
        test_cases = [
            (
                "expanding",
                {
                    "fruit": ["apple", "pear"],
                    "animal": ["cat", "dog"],
                    "include": [
                        {"color": "green"},
                        {"color": "pink", "animal": "cat"},
                        {"fruit": "apple", "shape": "circle"},
                        {"fruit": "banana"},
                        {"fruit": "banana", "animal": "cat"},
                    ],
                },
                [
                    {"fruit": "apple", "animal": "cat", "color": "pink", "shape": "circle"},
                    {"fruit": "apple", "animal": "dog", "color": "green", "shape": "circle"},
                    {"fruit": "pear", "animal": "cat", "color": "pink"},
                    {"fruit": "pear", "animal": "dog", "color": "green"},
                    {"fruit": "banana"},
                    {"fruit": "banana", "animal": "cat"},
                ],
            ),
            (
                "Example: Adding configurations",
                {
                    "os": ["ubuntu-latest", "macos-latest", "windows-latest"],
                    "version": [10, 12, 14],

                    "include": [
                        {"os": "windows-latest", "version": 17},
                    ],
                },
                [
                    {'os': 'ubuntu-latest', 'version': 10},
                    {'os': 'ubuntu-latest', 'version': 12},
                    {'os': 'ubuntu-latest', 'version': 14},
                    {'os': 'macos-latest', 'version': 10},
                    {'os': 'macos-latest', 'version': 12},
                    {'os': 'macos-latest', 'version': 14},
                    {'os': 'windows-latest', 'version': 10},
                    {'os': 'windows-latest', 'version': 12},
                    {'os': 'windows-latest', 'version': 14},
                    {'os': 'windows-latest', 'version': 17}
                ],
            ),
            (
                "adding: include only",
                {
                    "include": [
                        {"os": "windows-latest", "version": 17},
                        {"os": "ubuntu-latest", "version": 22},
                    ],
                },
                [
                    {"os": "windows-latest", "version": 17},
                    {"os": "ubuntu-latest", "version": 22},
                ],
            ),
        ]
        self.check_test_cases(test_cases)

    def test_matrix_conf_include_adding_includes_only(self):
        matrix_conf = {
            "include": [
                {"os": "windows-latest", "version": 17},
                {"os": "ubuntu-latest", "version": 22},
            ],
        }
        expected_jobs = [
            {"os": "windows-latest", "version": 17},
            {"os": "ubuntu-latest", "version": 22},
        ]
        jobs = matrix_conf_to_jobs(matrix_conf)
        print_list_diff(expected_jobs, jobs)
        self.assertEqual(expected_jobs, jobs)

    def test_matrix_conf_exclude(self):
        test_cases = [
            (
                "Excluding matrix configurations",
                {
                    "os": ["ubuntu-latest", "macos-latest", "windows-latest"],
                    "version": [12, 14, 16],
                    "environment": ["staging", "production"],
                    "exclude": [
                        {"os": "macos-latest", "version": 12, "environment": "production"},
                        {"os": "windows-latest", "version": 16},

                    ],
                },
                [
                    {"os": "ubuntu-latest", "version": 12, "environment": 'staging'},
                    {"os": "ubuntu-latest", "version": 12, "environment": 'production'},
                    {"os": "ubuntu-latest", "version": 14, "environment": 'staging'},
                    {"os": "ubuntu-latest", "version": 14, "environment": 'production'},
                    {"os": "ubuntu-latest", "version": 16, "environment": 'staging'},
                    {"os": "ubuntu-latest", "version": 16, "environment": 'production'},
                    {"os": "macos-latest", "version": 12, "environment": 'staging'},
                    {"os": "macos-latest", "version": 14, "environment": 'staging'},
                    {"os": "macos-latest", "version": 14, "environment": 'production'},
                    {"os": "macos-latest", "version": 16, "environment": 'staging'},
                    {"os": "macos-latest", "version": 16, "environment": 'production'},
                    {"os": "windows-latest", "version": 12, "environment": 'staging'},
                    {"os": "windows-latest", "version": 12, "environment": 'production'},
                    {"os": "windows-latest", "version": 14, "environment": 'staging'},
                    {"os": "windows-latest", "version": 14, "environment": 'production'},
                ],
            ),
        ]
        self.check_test_cases(test_cases)

    def test_include_jobs(self):
        test_cases = [
            (
                "none",
                [],
                [],
                []
            ),
            (
                "adding: include only",
                [],
                [
                    {"os": "windows-latest", "version": 17},
                    {"os": "ubuntu-latest", "version": 22},
                ],
                [
                    {"os": "windows-latest", "version": 17},
                    {"os": "ubuntu-latest", "version": 22},
                ],
            ),
            (
                "extend only",
                [{"os": "ubuntu-latest"}],
                [{"version": 12}],
                [{"os": "ubuntu-latest", "version": 12}]
            ),
            (
                "expand matching job",
                [{"os": "ubuntu-latest"}, {"os": "windows-latest"}],
                [{"os": "ubuntu-latest", "version": 12}],
                [
                    {"os": "ubuntu-latest", "version": 12},
                    {"os": "windows-latest"}
                ]
            ),
            (
                "Example: Expanding configurations",
                [{"os": "ubuntu-latest", "node": 14}, {"os": "ubuntu-latest", "node": 16},
                 {"os": "windows-latest", "node": 14}, {"os": "windows-latest", "node": 16}],
                [{"os": "windows-latest", "node": 16, "npm": 6}],
                [
                    {"os": "ubuntu-latest", "node": 14}, {"os": "ubuntu-latest", "node": 16},
                    {"os": "windows-latest", "node": 14}, {"os": "windows-latest", "node": 16, "npm": 6}
                ]
            ),
            (
                  "Expanding matrix configurations",
                [{"fruit": "apple", "animal": "cat"},{"fruit": "apple", "animal": "dog"},
                 {"fruit": "pear", "animal": "cat"},{"fruit": "pear", "animal": "dog"},],
                [
                    {"color": "green"},
                    {"animal": "cat", "color": "pink"},
                    {"fruit": "apple", "shape": "circle"},
                ],
                [
                  {"fruit": "apple", "animal": "cat", "color": "pink", "shape": "circle"},
                  {"fruit": "apple", "animal": "dog", "color": "green", "shape": "circle"},
                  {"fruit": "pear", "animal": "cat", "color": "pink"},
                  {"fruit": "pear", "animal": "dog", "color": "green"},
                ],
            ),
        ]
        for name, matrix, includes, expected_jobs in test_cases:
            with self.subTest(name):
                jobs = include_jobs(matrix, includes)
                print_list_diff(expected_jobs, jobs)
                self.assertEqual(expected_jobs, jobs)

    def test_include_adding_include_only(self):
        matrix = []
        includes = [
            {"os": "windows-latest", "version": 17},
            {"os": "ubuntu-latest", "version": 22},
        ]
        expected_jobs = includes

        jobs = include_jobs(matrix, includes)
        print_list_diff(expected_jobs, jobs)
        self.assertEqual(expected_jobs, jobs)


def main():
    print("hallo")


if __name__ == "__main__":
    main()
