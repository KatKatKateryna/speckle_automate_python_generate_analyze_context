from typing import List, Any
from specklepy.transports.server import ServerTransport
from specklepy.api.credentials import get_local_accounts
from specklepy.api import operations
from specklepy.api.operations import receive, send
from specklepy.api.client import SpeckleClient
from specklepy.objects import Base
from specklepy.objects.geometry import Polyline, Point, Mesh
from specklepy.objects.other import Collection
from specklepy.api.models import Branch
import importlib.metadata

print(importlib.metadata.version("specklepy"))

from flatten import flatten_base

host_server = "https://latest.speckle.dev/"  # project_data.speckle_server_url
stream_id = "aeb6aa8a6c"  # project_data.project_id
branch_name = "main"
# version_id = "5d720c0998" #project_data.version_id

account = get_local_accounts()[2]
client = SpeckleClient(host_server)
client.authenticate_with_token(account.token)


def pub_get_latest_objs(client: Any, stream_id: str, branch_name: str) -> object:
    """gets referencedObject from latest commit"""

    # client = SpeckleClient(host_server)
    # client.authenticate_with_token(access_token)
    branch = client.branch.get(stream_id, branch_name)
    latest_commit_obj = branch.commits.items[0]

    target_object_id = latest_commit_obj.referencedObject
    transport = ServerTransport(client=client, stream_id=stream_id)
    received = operations.receive(obj_id=target_object_id, remote_transport=transport)

    return received


def pub_get_all_objects(commit_collection: object) -> list:
    """Returns a list of Base objects from a Commit referencedObject"""

    all_objects = []

    try:
        for collection in commit_collection.elements:
            for element in collection.elements:
                all_objects.append(element)
                if element.elements:
                    all_objects.extend(element.elements)
    except Exception as e:
        print(e)  # "No elements found, aborting process.")
    # print(all_objects)
    return all_objects


def pub_send_objs_to_branch(source_objects: list):
    # authenticate
    # host_server = "https://speckle.xyz/"  # project_data.speckle_server_url
    # stream_id = "4a8fd0c6b6"  # project_data.project_id
    target_branch_name = "Space Syntax"
    account = get_local_accounts()[2]
    client = SpeckleClient(host_server)
    client.authenticate_with_token(account.token)

    # get or create branch
    branches = client.branch.list(stream_id)
    has_res_branch = any(b.name == target_branch_name for b in branches)
    if not has_res_branch:
        client.branch.create(stream_id, name=target_branch_name, description="")

    payload_objects = source_objects

    # append source objects to new Base
    payload_object = Base()
    payload_object["elements"] = payload_objects

    # send
    transport = ServerTransport(client=client, stream_id=stream_id)
    payload_object_id = operations.send(payload_object, [transport])

    commit_id = client.commit.create(
        stream_id,
        payload_object_id,
        target_branch_name,
        message="Commit",
    )

    return commit_id


base = pub_get_latest_objs(client, stream_id, branch_name)
obj = pub_get_all_objects(base)

commit_id = pub_send_objs_to_branch(obj)
print(commit_id)
