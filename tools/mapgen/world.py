"""Conteneur de la map : brushes du monde, func_detail par groupe, entites."""
import contextlib

from . import geom


class Entity:
    def __init__(self, classname, kv, brushes=None, group=None):
        self.classname = classname
        self.kv = kv
        self.brushes = brushes or []
        self.group = group


def fmt_vec(v):
    return " ".join(_num(c) for c in v)


def _num(c):
    c = float(c)
    if abs(c - round(c)) < 1e-6:
        return str(int(round(c)))
    return f"{c:.3f}".rstrip("0").rstrip(".")


class World:
    def __init__(self):
        self.world = []
        self.entities = []
        self.detail = {}
        self.visgroups = []
        self._group = "Divers"
        self.markers = []  # points d'interet (pour la carte / la doc)

    @contextlib.contextmanager
    def group(self, name):
        old = self._group
        self._group = name
        if name not in self.visgroups:
            self.visgroups.append(name)
        try:
            yield
        finally:
            self._group = old

    def add(self, *brushes):
        lst = self.detail.setdefault(self._group, [])
        for b in brushes:
            if isinstance(b, (list, tuple)):
                lst.extend(b)
            else:
                lst.append(b)
        return brushes[0] if len(brushes) == 1 else brushes

    def add_world(self, *brushes):
        for b in brushes:
            self.world.append(b)

    def ent(self, classname, origin=None, brushes=None, **kv):
        d = {}
        if origin is not None:
            d["origin"] = fmt_vec(origin)
        for k, v in kv.items():
            k = k.rstrip("_")
            if isinstance(v, (tuple, list)):
                v = fmt_vec(v)
            d[k] = str(v)
        if brushes is not None and not isinstance(brushes, (list, tuple)):
            brushes = [brushes]
        e = Entity(classname, d, list(brushes or []), self._group)
        self.entities.append(e)
        return e

    def light(self, origin, color=(255, 220, 180), bright=300, fifty=None, zero=None):
        kv = {"_light": f"{color[0]} {color[1]} {color[2]} {bright}"}
        if fifty:
            kv["_fifty_percent_distance"] = fifty
            kv["_zero_percent_distance"] = zero or fifty * 2
        return self.ent("light", origin, **kv)

    def prop(self, model, origin, yaw=0, solid=6, skin=0, fade=(2500, 3200)):
        return self.ent("prop_static", origin, model=model, angles=(0, yaw, 0),
                        solid=solid, skin=skin, disableshadows=0,
                        fademindist=fade[0], fademaxdist=fade[1], fadescale=1)

    def marker(self, name, pos, kind="lieu"):
        self.markers.append({"name": name, "pos": [float(p) for p in pos], "kind": kind,
                             "group": self._group})

    def counts(self):
        nd = sum(len(v) for v in self.detail.values())
        nb = sum(len(e.brushes) for e in self.entities)
        sides = sum(len(b.faces) for v in self.detail.values() for b in v)
        sides += sum(len(b.faces) for b in self.world)
        sides += sum(len(b.faces) for e in self.entities for b in e.brushes)
        return {
            "world_brushes": len(self.world),
            "detail_brushes": nd,
            "entity_brushes": nb,
            "total_brushes": len(self.world) + nd + nb,
            "brush_sides": sides,
            "entities": len(self.entities),
        }


# raccourci pratique
B = geom
