from dataclasses import is_dataclass, asdict


def to_dict(obj):
    # 1. None 或 基础类型
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # 2. dataclass
    if is_dataclass(obj):
        return asdict(obj)

    # 3. pydantic 模型
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return obj.dict()

    # 4. 普通类（有 __dict__）
    if hasattr(obj, "__dict__"):
        return {k: to_dict(v) for k, v in vars(obj).items()}

    # 5. __slots__ 类
    if hasattr(obj, "__slots__"):
        return {slot: to_dict(getattr(obj, slot)) for slot in obj.__slots__}

    # 6. 容器类型：list / tuple / set / dict
    if isinstance(obj, (list, tuple, set)):
        return [to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}

    # 7. 其他类型（直接转 str）
    return str(obj)
