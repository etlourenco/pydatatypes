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

from abc import ABC, abstractmethod
from functools import cache
from typing import Generic, TypeVar


class data_addr(ABC):
    @abstractmethod
    def resolve(self) -> int:
        pass

class data_addr_absolute(data_addr):
    def __init__(self, addr: int) -> None:
        super().__init__()
        self._addr = addr
    
    def resolve(self) -> int:
        return self._addr

class data_addr_offset(data_addr):
    def __init__(self, ref: data_addr, offset: int) -> None:
        super().__init__()
        self._offset = offset
        self._ref = ref

    def resolve(self) -> int:
        return self._ref.resolve() + self._offset













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
    def __init__(self, addr: data_addr) -> None:
        super().__init__()
        self._addr = addr

    # TODO: check better way to handle address considering: absolute/offset, cache, strategy, static/pointer
    # idea 01) create class to represent object, could be like absolute (constant), offset from (other address object), from external source
    def addressof(self) -> data_addr:
        return self._addr
    


                








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
    def value_set(self, val: int) -> None:
        self._val = val # TODO: for now we create local data member to hold value

    def value_get(self) -> int:
        return self._val # TODO: see above
    





class u8_t(int_t):
    _size = 1

class u16_t(int_t):
    _size = 2

class u32_t(int_t):
    _size = 4

class u64_t(int_t):
    _size = 8

class intptr_t(u64_t):
    pass








class struct_t(data_t):
    _is_packed: bool = False # _packing: Optional[int] = None
    _members: dict[str, type[data_t]]

    # type (class) methods
    @classmethod
    @cache
    def sizeof(cls) -> int:
        name, t = list(cls._members.items())[-1]
        non_padded_size = cls._member_offsets()[name] + t.sizeof()
        return non_padded_size if cls._is_packed else non_padded_size + (cls.alignof() - (non_padded_size % cls.alignof())) % cls.alignof()

    @classmethod
    @cache
    def alignof(cls) -> int:
        return 1 if cls._is_packed else max(t.alignof() for t in cls._members.values())
    
    # helpers
    @classmethod
    @cache
    def _member_offsets(cls) -> dict[str, int]:
        offset = 0
        def get_incremental_offset(member_t: type[data_t]) -> int:
            nonlocal offset
            member_offset = offset if cls._is_packed else offset + (member_t.alignof() - (offset % member_t.alignof())) % member_t.alignof()
            offset = member_offset + member_t.sizeof()
            return member_offset  
        return {name: get_incremental_offset(t) for name, t in cls._members.items()}

    # instance (object) methods
    def __init__(self, addr: data_addr) -> None:
        super().__init__(addr)
        self._instances = {name: t(data_addr_offset(self.addressof(), self._member_offsets()[name])) for name, t in self._members.items()}





ptr_data_t = TypeVar("ptr_data_t", bound=data_t)


class pointer_t(intptr_t, Generic[ptr_data_t]):
    # instance (object) methods
    def __init__(self, addr: int, ptr_type: type[ptr_data_t]) -> None:
        super().__init__(addr)
        self._ptr_type = ptr_type

    def dereference(self) -> ptr_data_t:
        return self._ptr_type(data_addr_absolute(self.value_get()))











class my_t(struct_t):
    _members = {
        "a": u16_t,
        "b": u32_t,
        "c": u16_t,
    }

class my_t_packed(my_t):
    _is_packed = True





a = list()



aa = u32_t(data_addr_absolute(1000))
aa.value_set(123456)

bb = pointer_t(data_addr_absolute(0), u32_t)
bb.value_set(aa.addressof().resolve())
cc = bb.dereference()


ee = my_t(data_addr_absolute(10000))
ee0 = ee._instances["b"].addressof()
ee1 = ee0.resolve()



def get_pointed_value(ptr: pointer_t[u32_t]) -> int:
    pointed_var = ptr.dereference()
    return pointed_var.value_get()

lala = get_pointed_value(bb)


pass




