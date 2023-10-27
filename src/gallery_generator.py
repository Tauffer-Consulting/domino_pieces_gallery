import json
import os
from clients.github_rest_client import GithubRestClient
import tomli


class GalleryGenerator:
    def __init__(self):
        self.github_client = GithubRestClient(token=os.environ["GITHUB_TOKEN"])

    def _read_release_data_from_github(
        self, 
        path: str, 
        commit_sha_ref: str
    ) -> dict:
        """Read files from a specific version of repository in github

        Args:
            path (str): Repository path
            commit_sha_ref (str): Release commit sha reference

        Raises:
            ResourceNotFoundException: If tag version is not found raise exception

        Returns:
            dict: dictionary containing repository data with the following keys:
                - dependencies_map: dependencies_map file data
                - compiled_metadata: compiled_metadata file data
                - config_toml: config_toml file data
        """

        compiled_metadata = self.github_client.get_contents(
            repo_name=path,
            file_path='.domino/compiled_metadata.json',
            commit_sha=commit_sha_ref
        )
        compiled_metadata = json.loads(compiled_metadata.decoded_content.decode('utf-8'))

        config_toml = self.github_client.get_contents(
            repo_name=path,
            file_path='config.toml',
            commit_sha=commit_sha_ref
        )
        config_toml = tomli.loads(config_toml.decoded_content.decode('utf-8'))

        data = {
            "compiled_metadata": compiled_metadata,
            "config_toml": config_toml
        }
        return data


    def get_repository_last_release_data(self, repository: dict):
        """
        Get the last release data from a repository.

        Args:
            repository (dict): A dictionary containing the repository data.

        Returns:
            dict: A dictionary containing the last release data.
        """

        repository_path = repository["url"].split("github.com/")[1]
        releases = self.github_client.get_releases(repo_name=repository_path)
        if not releases:
            raise Exception(f"Repository {repository['name']} has no releases.")

        last_release = releases[0]
        commit_sha_ref = str(last_release.target_commitish)
        release_data = self._read_release_data_from_github(
            path=repository_path,
            commit_sha_ref=commit_sha_ref
        )
        return release_data
        

    def create_gallery_json(self, update_gallery: bool = True):
        """
        Create the gallery.json file from the repositories.json file.

        Args:
            update_gallery (bool, optional): If true it will update all repositories from gallery, 
                                            if False it will only add the new ones.
                                            Defaults to True.
        """

        with open("gallery.json", "r") as f:
            current_gallery = json.load(f)
        
        with open("repositories.json", "r") as f:
            repositories = json.load(f)

        output_gallery = {}
        # Using set for validation, we can't have duplicate urls or names
        urls = set()
        names = set()
        for repository in repositories:
            if not update_gallery and repository['name'] in current_gallery:
                print(f"Repository {repository['name']} already in gallery, skipping...")
                continue

            if repository["url"] in urls:
                print(f"Duplicate repository url: {repository['url']}, skipping...")
                continue
            if repository["name"] in names:
                print(f"Duplicate repository name: {repository['name']}, skipping...")
                continue
            
            repository_release_data = self.get_repository_last_release_data(repository=repository)
            repository_name = repository_release_data.get("config_toml").get("repository").get("REPOSITORY_NAME")
            if repository_name != repository["name"]:
                print(f"Repository name mismatch: {repository_name} != {repository['name']}, skipping...")
                continue
    
            repository_version = repository_release_data.get("config_toml").get("repository").get("VERSION")
            repository_url = repository["url"]

            output_gallery[repository_name] = {
                "version": repository_version,
                "url": repository_url,
                "pieces": repository_release_data.get('compiled_metadata', {})
            }
            urls.add(repository["url"])
            names.add(repository["name"])

        with open("gallery.json", "w") as f:
            json.dump(output_gallery, f, indent=4)



if __name__ == '__main__':
    generator = GalleryGenerator()
    generator.create_gallery_json(update_gallery=True)
