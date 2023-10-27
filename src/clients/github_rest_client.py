from github import Github, GithubException


class GithubRestClient(Github):
    def __init__(self, token: str):
        super().__init__(token)

    def get_releases(self, repo_name: str):
        """
        Get all releases from a repository.
        """
        repo = super().get_repo(repo_name)
        releases = [e for e in repo.get_releases()]
        return releases


    def get_contents(self, repo_name: str, file_path: str, commit_sha: str = None):
        """
        Get the contents of a file from a repository for a specific commit hash.
        If the hash is not defined, the latest commit is used.
        """
        try:
            repo = super().get_repo(repo_name)
            if not commit_sha:
                contents = repo.get_contents(file_path)
                return contents
            contents = repo.get_contents(file_path, ref=commit_sha)
            return contents
        except GithubException as e:
            self._handle_exceptions(e)
    
    def create_file(self, repo_name: str, file_path: str, content: str):
        """
        Create a file in a repository.
        """
        repo = super().get_repo(repo_name)
        commit_msg = 'Create file'
        repo.create_file(
            path=file_path, 
            message=commit_msg, 
            content=content
        )


