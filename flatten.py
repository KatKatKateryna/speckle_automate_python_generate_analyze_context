from typing import Iterable, List
from specklepy.objects import Base
from specklepy.objects.geometry import Mesh


def flatten_base(base: Base) -> Iterable[Base]:
    if hasattr(base, "elements"):
        for element in base.elements:
            yield from flatten_base(element)
    yield base

def iterateBase(base: Base) -> Iterable[Base]:
    meshes = []
    if isinstance(base, Base):
        for name in base.get_member_names():
            try:
                if name.endswith("definition") or name == "units" or name == "speckle_type":
                    continue
                if isinstance(base[name], Mesh): 
                    meshes.append(meshes)
                elif isinstance(base[name], List) and isinstance(base[name][0], Mesh): 
                    [ meshes.append(obj) for obj in base[name] if isinstance(obj, Mesh) ]
                elif isinstance(base[name], Base): 
                    meshes.extend(iterateBase(base[name]))
                elif isinstance(base[name], List): 
                    meshes.extend(iterateBase(base[name]))
            except: pass
    elif isinstance(base, List):
        for item in base:
            meshes.extend(iterateBase(item))
    return meshes 
