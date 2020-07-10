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


def replace_chunk(content, marker, chunk):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    chunk = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)

    return r.sub(chunk, content)


if __name__ == "__main__":
    with open("README.md") as readme:
        readme_contents = readme.read()

    releases = recent_releases()
    releases_md = "\n".join(
        [
            "* [{repo} {release}]({url}) - {published}".format(**release)
            for release in releases
        ]
    )
    rewritten = replace_chunk(readme_contents, "recent_releases", releases_md)

    posts = recent_posts()
    posts_md = "\n".join(["* [{title}]({link})".format(**post) for post in posts])
    rewritten = replace_chunk(rewritten, "blog", posts_md)

    with open("README.md", "w") as readme:
        readme.write(rewritten)
