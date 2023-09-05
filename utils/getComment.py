
from typing import Any, Dict
from specklepy.api.client import SpeckleClient
from gql import gql

def get_comments(
    client: SpeckleClient,
    project_id: str,
) -> Dict[str, Any]:
    return client.httpclient.execute(
        gql("""
            query c{ """ 
            + f'comments(streamId:"{project_id}")' +
                """{
                    items {
                    id
                    rawText
                    viewerState
                    }
                }
            }
            """
        )
    )