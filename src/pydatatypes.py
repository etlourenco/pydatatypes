# == type:
# size
# align
# * format
# * element offset
# * numeric limits
# 
# == variable:
# address
# * value
# * to/from bytes
#
from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from functools import cache
from typing import Generic, TypeVar, Any, Callable













# TODO: check best way to handle address considering: absolute/offset, cache, strategy, static/pointer
# idea 01) create class to represent object, could be like absolute (constant), offset from (other address object), from external source
class data_addr(ABC):
    @abstractmethod
    def resolve(self) -> int:
        pass


# TODO: null address?


class data_addr_absolute(data_addr):
    def __init__(self, addr: int) -> None:
        super().__init__()
        self._addr = addr
    
    def resolve(self) -> int:
        return self._addr


class data_addr_offset(data_addr):
    def __init__(self, ref: data_addr, offset: int) -> None:
        super().__init__()
        self._ref = ref
        self._offset = offset

    def resolve(self) -> int:
        return self._ref.resolve() + self._offset

















class data_manager(ABC):
    @abstractmethod
    def create(self, t: type[generic_data_t]) -> generic_data_t:
        pass
    
    @abstractmethod
    def destroy(self, obj: data_t) -> None:
        pass

    @abstractmethod
    def read_value(self, obj: data_t) -> Any:
        pass

    @abstractmethod
    def write_value(self, obj: data_t, value: Any) -> None:
        pass


# TODO: null manager?


class self_data_manager(data_manager):
    def __init__(self) -> None:
        super().__init__()
        self._addr_count: int = 0

    def create(self, t: type[generic_data_t]) -> generic_data_t:
        obj = t(data_addr_absolute(self._addr_count), self)
        obj._value: Any = None
        self._addr_count += t.sizeof()
        return obj
    
    def destroy(self, obj: data_t) -> None:
        del obj._value
        
    def read_value(self, obj: data_t) -> Any:
        if hasattr(obj, "_value"):
            return obj._value
        else:
            raise Exception("Cannot read value from destroyed object.")

    def write_value(self, obj: data_t, value: Any) -> None:
        if hasattr(obj, "_value"):
            obj._value = value
        else:
            raise Exception("Cannot write value to destroyed object.")


default_data_manager: data_manager = self_data_manager()















class data_t(ABC):
    # type (class) methods    
    @classmethod
    @abstractmethod
    def sizeof(cls) -> int:
        pass

    @classmethod
    @abstractmethod
    def alignof(cls) -> int:
        pass

    # instance (object) methods
    def __init__(self, addr: data_addr, mgr: data_manager) -> None:
        super().__init__()
        self._addr = addr
        self._mgr = mgr

    def addressof(self) -> data_addr:
        return self._addr
    
    def read_value(self) -> Any:
        return self._mgr.read_value(self)

    def write_value(self, value: Any) -> None:
        self._mgr.write_value(self, value)

generic_data_t = TypeVar("generic_data_t", bound=data_t)



                











class int_t(data_t):
    _size: int

    # type (class) methods
    @classmethod
    @cache
    def sizeof(cls) -> int:
        return cls._size
    
    @classmethod
    @cache
    def alignof(cls) -> int:
        return cls._size
    
    # instance (object) methods
    def read_value(self) -> int:
        return super().read_value()

    def write_value(self, value: int) -> None:
        super().write_value(value)


class u8_t(int_t):
    _size = 1

class u16_t(int_t):
    _size = 2

class u32_t(int_t):
    _size = 4

class u64_t(int_t):
    _size = 8





















# TODO: >>>>>>>>>>>>>>>>>>>>>> bitfields <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# TODO: >>>>>>>>>>>>>>>>>>>>>> arrays <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<



















#
#   CURRENTLY DOESN'T SUPPORT EMPTY STRUCTS, BUT I THINK IT COULD
#
class struct_t(data_t):
    _is_packed: bool = False # _packing: Optional[int] = None

    # type (class) methods
    @classmethod
    @cache
    def sizeof(cls) -> int:
        name, t = list(cls._members().items())[-1]
        non_padded_size = cls._member_offsets()[name] + t.sizeof()
        return non_padded_size if cls._is_packed else non_padded_size + (cls.alignof() - (non_padded_size % cls.alignof())) % cls.alignof()

    @classmethod
    @cache
    def alignof(cls) -> int:
        return 1 if cls._is_packed else max(t.alignof() for t in cls._members().values())

    @classmethod
    @cache
    def offsetof(cls, member: str) -> int:
        return cls._member_offsets()[member]

    # helpers
    @classmethod
    @cache
    def _members(cls) -> dict[str, type[data_t]]:
        return {name: value for name, value in vars(cls).items() if isinstance(value, type) and issubclass(value, data_t)}

    @classmethod
    @cache
    def _member_offsets(cls) -> dict[str, int]:
        offset = 0
        def get_incremental_offset(member_t: type[data_t]) -> int:
            nonlocal offset
            member_offset = offset if cls._is_packed else offset + (member_t.alignof() - (offset % member_t.alignof())) % member_t.alignof()
            offset = member_offset + member_t.sizeof()
            return member_offset  
        return {name: get_incremental_offset(t) for name, t in cls._members().items()}

    # instance (object) methods
    def __init__(self, addr: data_addr, mgr: data_manager) -> None:
        super().__init__(addr, mgr)
        for name, t in self._members().items():
            setattr(self, name, t(data_addr_offset(self.addressof(), self.offsetof(name)), mgr))


#
#   DECORATOR FOR STRUCT DOESN'T SEEM GOOD
#       PROS: ALLOW TO INSTANTIATE CLASS MEMEBERS BASED ON ANNOTATIONS
#       CONS: CAN'T SEEM TO ANNOTATE RETURN TO BE CHILD OF STRUCT AND ARUMENT AS WELL
#
#   MAYBE THIS IS A CASE FOR METACLASS?
#
# strcut_type = TypeVar("strcut_type")
# def struct_t_(cls: strcut_type) -> strcut_type:
# def struct_t_(cls) -> type[struct_t]:
#     return type(cls.__name__, (struct_t,), {name: globals()[t_name] for name, t_name in cls.__annotations__.items()})


#
#   DECORATOR FOR STRUCT DOESN'T SEEM GOOD
#       PROS: INHERITS FROM STRUCT_T (WITH ALL INTERFACE) ADDING MEMBER DEFINITIONS AS ONE-LINERS
#       CONS: LITTLE CONVOLUTED/REPEATED SYNTAX ON MEMBER DEFINITIONS
#
#   MAYBE THIS IS A CASE FOR METACLASS?
#
class my_struct_1(struct_t):
    _ccc: u16_t = u16_t
    _bbb: u32_t = u32_t
    _aaa: u16_t = u16_t

class my_struct_2(struct_t):
    pass














# instanciate a concrete pointer type to defined "ptr_type"
# @cache # this seems to screw up type annotation, keep commented for now
def ptr_(ptr_type: type[generic_data_t]) -> type[base_ptr_t[generic_data_t]]:
    return type(f"ptr_{ptr_type.__name__}", (base_ptr_t,), dict(_ptr_type=ptr_type))

class intptr_t(int_t):
    _size = 8

# template pointer class pointing to generic "_ptr_type"
class base_ptr_t(intptr_t, Generic[generic_data_t]):
    _ptr_type: type[generic_data_t]
    
    def __init__(self, addr: data_addr, mgr: data_manager) -> None:
        assert hasattr(self, "_ptr_type"), 'Cannot instantiate directly "base_ptr_t" without defined "_ptr_type". Use "ptr_(ptr_type)(addr, mgr)" to instantiate pointer to defined "ptr_type".'
        super().__init__(addr, mgr)

    def dereference(self) -> generic_data_t:
        return self._ptr_type(self.read_value(), self._mgr)





















pass