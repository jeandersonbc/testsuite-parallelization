import os


def build_task(*additional_args):
    args = ["mvn", "clean", "install"]
    if additional_args:
        args.extend(additional_args)
    return args


def test_task(*additional_args):
    args = ["mvn", "test"]
    if additional_args:
        args.extend(additional_args)
    return args


def resolve_dependencies_task():
    """
    Task arguments to ensure dependencies are resolved before running in offline mode
    :return: List of arguments to run in a system call
    """
    return ["mvn", "dependency:go-offline"]


def is_valid_project(subject_path):
    """
    Checks if the informed path is a valid Maven project
    :param subject_path: the path to verify
    :return: true if the informed path contains a pom.xml file (false otherwise).
    """
    return os.path.exists(os.path.join(subject_path, "pom.xml"))