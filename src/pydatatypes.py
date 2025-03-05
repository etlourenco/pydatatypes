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


#
#
#   CACHE SEEMS TO BE SCREWING-UP TYPE ANNOTATION FOR BITFIELD, ARRAY AND POINTER TYPE FACTORIES.
#   NEED TO DEFINE METHODS FOR ITERATING ON STRUCTURES, LOOKS LIKE SHOULD BE SOMEWHAT SIMILAR TO PYTHON DICT'S
#   TODO: add parent, add name, bitfield group é mais pra struct q pra int (fazer tipo proprio), loopar: "members()", "names()", "values()"?
#
#





from __future__ import annotations
from abc import ABC, abstractmethod
from functools import cache
from typing import Generic, TypeVar, Any





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


@cache
def data_manager_null() -> data_manager:
    class data_manager_null_t(data_manager):
        def create(self, t: type[generic_data_t]) -> generic_data_t:
            raise Exception("data_manager_null_t.create")
        def destroy(self, obj: data_t) -> None:
            raise Exception("data_manager_null_t.destroy")
        def read_value(self, obj: data_t) -> Any:
            raise Exception("data_manager_null_t.read_value")
        def write_value(self, obj: data_t, value: Any) -> None:
            raise Exception("data_manager_null_t.write_value")
    return data_manager_null_t()





class data_addr(ABC):
    @abstractmethod
    def resolve(self) -> int:
        pass

    def __init__(self, mgr: data_manager) -> None:
        super().__init__()
        self._mgr = mgr
    
    def get_manager(self) -> data_manager:
        return self._mgr


@cache
def data_addr_null() -> data_addr:
    class data_addr_null_t(data_addr):
        def resolve(self) -> int:
            raise Exception("data_addr_null_t.resolve")
    return data_addr_null_t(data_manager_null())


class data_addr_absolute(data_addr):
    def __init__(self, addr: int, mgr: data_manager) -> None:
        super().__init__(mgr)
        self._addr = addr
    
    def resolve(self) -> int:
        return self._addr


class data_addr_offset(data_addr):
    def __init__(self, ref: data_addr, offset: int) -> None:
        super().__init__(ref.get_manager())
        self._ref = ref
        self._offset = offset

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

    @classmethod
    @cache
    def bit_length(cls) -> int:
        return cls.sizeof() * 8
    
    # instance (object) methods
    def __init__(self, addr: data_addr) -> None:
        super().__init__()
        self._addr = addr

    def addressof(self) -> data_addr:
        return self._addr
    
    def read_value(self) -> Any:
        return self._addr.get_manager().read_value(self)

    def write_value(self, value: Any) -> None:
        self._addr.get_manager().write_value(self, value)


generic_data_t = TypeVar("generic_data_t", bound=data_t)





class int_t(data_t):
    _size: int
    _signed: bool

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
    _signed = False


class u16_t(int_t):
    _size = 2
    _signed = False


class u32_t(int_t):
    _size = 4
    _signed = False


class u64_t(int_t):
    _size = 8
    _signed = False


generic_int_t = TypeVar("generic_int_t", bound=int_t)





# instanciate a concrete bitfield type of underlying_type and "_bit_length"
bitfield_cache: dict[tuple[type[generic_int_t], int], type[base_bitfield_t[generic_int_t]]] = dict()


def bitfield_(underlying_type: type[generic_int_t], bit_len: int) -> type[base_bitfield_t[generic_int_t]]:
    try:
        return bitfield_cache[(underlying_type, bit_len)]
    except KeyError:
        bitfield_cache[(underlying_type, bit_len)] = type(
            f"bitfield_{underlying_type.__name__}_{bit_len}b",
            (base_bitfield_t,),
            dict(_size=underlying_type._size, _signed=underlying_type._signed, _bit_length=bit_len)
        )
        return bitfield_cache[(underlying_type, bit_len)]


class base_bitfield_t(int_t, Generic[generic_int_t]):
    _bit_length: int

    # type (class) methods
    @classmethod
    @cache
    def bit_length(cls) -> int:
        return cls._bit_length


class base_bitfield_group_t(int_t):
    _members: dict[str, type[base_bitfield_t]]
    _group_counter: int = 0

    @classmethod
    def add_member(cls, member_name: str, member_type: type[base_bitfield_t]) -> type[base_bitfield_group_t]:
        if cls == base_bitfield_group_t or cls._size != member_type._size or cls._signed != member_type._signed or (cls.bit_length() - sum(m.bit_length() for m in cls._members.values())) < member_type.bit_length():
            group = type(
                f"bitfield_group_{base_bitfield_group_t._group_counter}_t",
                (base_bitfield_group_t,),
                dict(_size=member_type._size, _signed=member_type._signed, _members={member_name:member_type})
            )
            base_bitfield_group_t._group_counter += 1
            return group
        else:
            cls._members[member_name] = member_type
            return cls

    # instance (object) methods
    def __init__(self, addr: data_addr) -> None:
        super().__init__(addr)
        self._instances = {name: t(self.addressof()) for name, t in self._members.items()}

    def instances(self) -> dict[str, base_bitfield_t]: # TODO: see top
        return self._instances





#
#   CURRENTLY DOESN'T SUPPORT EMPTY STRUCTS, BUT I THINK IT COULD
#
class struct_t(data_t):
    _is_packed: bool = False # _packing: Optional[int] = None

    # type (class) methods
    @classmethod
    @cache
    def sizeof(cls) -> int:
        name, t = list(cls._member_types().items())[-1]
        non_padded_size = cls._member_offsets()[name] + t.sizeof()
        return non_padded_size if cls._is_packed else non_padded_size + (cls.alignof() - (non_padded_size % cls.alignof())) % cls.alignof()

    @classmethod
    @cache
    def alignof(cls) -> int:
        return 1 if cls._is_packed else max(t.alignof() for t in cls._member_types().values())

    @classmethod
    @cache
    def offsetof(cls, member: str) -> int:
        return cls._member_offsets()[member]

    # helpers
    # @classmethod
    # @cache
    # def _create_member_attributtes_from_annotations(cls) -> None:
    #     for name, typename in cls.__annotations__.items():
    #         typename_args = [s for s in re.split(r'[\[\], ]', typename) if s]
    #         if len(typename_args) < 2:
    #             setattr(cls, name, globals()[typename])
    #         else:
    #             match typename_args[0]:
    #                 case 'base_bitfield_t':
    #                     setattr(cls, name, bitfield_(*typename_args[1:]))
    #                 case 'base_ptr_t':
    #                     setattr(cls, name, ptr_(*typename_args[1:]))
    #                 case 'base_array_t':
    #                     setattr(cls, name, array_(*typename_args[1:]))
    #                 case _:
    #                     raise Exception("WRONG!!")

    @classmethod
    @cache
    def _member_types(cls) -> dict[str, type[data_t]]:
        # cls._create_member_attributtes_from_annotations()
        member_types: dict[str, type[data_t]] = dict()
        bitfield_group = base_bitfield_group_t
        for name, value in vars(cls).items():
            if isinstance(value, type) and issubclass(value, data_t):
                if not issubclass(value, base_bitfield_t):
                    if bitfield_group != base_bitfield_group_t:
                        member_types[bitfield_group.__name__] = bitfield_group
                        bitfield_group = base_bitfield_group_t
                    member_types[name] = value
                else:
                    new_group = bitfield_group.add_member(name, value)
                    if new_group != bitfield_group and bitfield_group != base_bitfield_group_t:
                        member_types[bitfield_group.__name__] = bitfield_group
                    bitfield_group = new_group
        if bitfield_group != base_bitfield_group_t:
            member_types[bitfield_group.__name__] = bitfield_group
        return member_types

    @classmethod
    @cache
    def _member_offsets(cls) -> dict[str, int]:
        offset = 0
        def get_incremental_offset(member_t: type[data_t]) -> int:
            nonlocal offset
            member_offset = offset if cls._is_packed else offset + (member_t.alignof() - (offset % member_t.alignof())) % member_t.alignof()
            offset = member_offset + member_t.sizeof()
            return member_offset  
        return {name: get_incremental_offset(t) for name, t in cls._member_types().items()}

    # instance (object) methods
    def __init__(self, addr: data_addr) -> None:
        super().__init__(addr)
        self.bitfield_group_instances: dict[str, base_bitfield_group_t] = dict()
        for name, t in self._member_types().items():
            if not issubclass(t, base_bitfield_group_t):
                setattr(self, name, t(data_addr_offset(self.addressof(), self.offsetof(name))))
            else:
                self.bitfield_group_instances[name] = t(data_addr_offset(self.addressof(), self.offsetof(name))) # is this needed or bitfield instances maybe should only have their group type?
                for bitfield_name, bitfield_t in self.bitfield_group_instances[name].instances().items():
                    setattr(self, bitfield_name, bitfield_t)


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
#   INHERITANCE FOR STRUCT DOESN'T SEEM GOOD
#       PROS: INHERITS FROM STRUCT_T (WITH ALL INTERFACE) ADDING MEMBER DEFINITIONS AS ONE-LINERS
#       CONS: LITTLE CONVOLUTED/REPEATED SYNTAX ON MEMBER DEFINITIONS
#
#   MAYBE THIS IS A CASE FOR METACLASS?
#
# class my_struct_1(struct_t):
#     _ccc: u16_t = u16_t
#     _bbb: u32_t = u32_t
#     _aaa: u16_t = u16_t





# instanciate a concrete pointer type to defined "ptr_type"
ptr_cache: dict[type[generic_data_t], type[base_ptr_t[generic_data_t]]] = dict()


def ptr_(ptr_type: type[generic_data_t]) -> type[base_ptr_t[generic_data_t]]:
    try:
        return ptr_cache[ptr_type]
    except KeyError:
        ptr_cache[ptr_type] = type(f"ptr_{ptr_type.__name__}", (base_ptr_t,), dict(_ptr_type=ptr_type))
        return ptr_cache[ptr_type]


class intptr_t(int_t):
    _size = 8
    _signed = False


# template pointer class pointing to generic "_ptr_type"
class base_ptr_t(intptr_t, Generic[generic_data_t]):
    _ptr_type: type[generic_data_t]
    
    def __init__(self, addr: data_addr) -> None:
        assert hasattr(self, "_ptr_type"), 'Cannot instantiate directly "base_ptr_t" without defined "_ptr_type". Use "ptr_(ptr_type)(addr, mgr)" to instantiate pointer to defined "ptr_type".'
        super().__init__(addr)

    def dereference(self) -> generic_data_t:
        return self._ptr_type(data_addr_absolute(self.read_value(), self.addressof().get_manager()))





# instanciate a concrete array type of "_element_type" and "_length"
array_cache: dict[tuple[type[generic_data_t], int], type[base_array_t[generic_data_t]]] = dict()


def array_(elem_type: type[generic_data_t], array_len: int) -> type[base_array_t[generic_data_t]]:
    try:
        return array_cache[(elem_type, array_len)]
    except KeyError:
        array_cache[(elem_type, array_len)] = type(f"array_{elem_type.__name__}_{array_len}", (base_array_t,), dict(_element_type=elem_type, _length=array_len))
        return array_cache[(elem_type, array_len)]


# template array class of generic type "_element_type" and length "_length"
class base_array_t(data_t, Generic[generic_data_t]):
    _element_type: type[generic_data_t]
    _length: int

    # type (class) methods
    @classmethod
    @cache
    def sizeof(cls) -> int:
        return cls._element_type.sizeof() * cls._length

    @classmethod
    @cache
    def alignof(cls) -> int:
        return cls._element_type.alignof()

    # instance (object) methods
    def __init__(self, addr: data_addr) -> None:
        assert hasattr(self, "_element_type"), 'Cannot instantiate directly "base_array_t" without defined "_element_type". Use "XXX(element_type, length)(addr, mgr)" to instantiate array of type "element_type".'
        assert hasattr(self, "_length"), 'Cannot instantiate directly "base_array_t" without defined "_length". Use "XXX(ptr_type)(element_type, length)" to instantiate array of "length".'
        super().__init__(addr)
        self._elements = [self._element_type(data_addr_offset(self.addressof(), i * self._element_type.sizeof())) for i in range(self._length)]

    def __getitem__(self, i: int) -> generic_data_t:
        return self._elements[i]




