from datetime import datetime
import re
import os

from python_graphql_client import GraphqlClient
import feedparser


TOKEN = os.getenv("GITHUB_TOKEN")


def recent_releases():
    query = """
    query {
        viewer {
            repositories(first: 100, privacy: PUBLIC) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
                name
                releases(last:1) {
                totalCount
                nodes {
                    name
                    publishedAt
                    url
                }
                }
            }
            }
        }
    }
    """

    client = GraphqlClient(endpoint="https://api.github.com/graphql")
    data = client.execute(
        query=query, headers={"Authorization": "Bearer {}".format(TOKEN)}
    )

    releases = []
    repos = set()

    for repo in data["data"]["viewer"]["repositories"]["nodes"]:
        if repo["releases"]["totalCount"] and repo["name"] not in repos:
            repos.add(repo["name"])
            releases.append(
                {
                    "repo": repo["name"],
                    "release": repo["releases"]["nodes"][0]["name"],
                    "url": repo["releases"]["nodes"][0]["url"],
                    "published": repo["releases"]["nodes"][0]["publishedAt"].split("T")[
                        0
                    ],
                }
            )

    releases = sorted(releases, key=lambda r: r["published"], reverse=True,)

    return releases[:5]


def recent_posts():
    posts = feedparser.parse("https://ege.dev/index.xml")["entries"]

    return posts[:5]


if __name__ == "__main__":
    releases = recent_releases()
    posts = recent_posts()

    with open("README.md", "w") as readme:
        readme.write("### Recent releases\n\n")
        releases_md = "\n".join(
            [
                "* [{repo} {release}]({url}) - {published}".format(**release)
                for release in releases
            ]
        )
        readme.write(releases_md)
        readme.write("\n\n### Recent posts\n\n")
        posts_md = "\n".join(["* [{title}]({link})".format(**post) for post in posts])
        readme.write(posts_md)
