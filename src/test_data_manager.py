from pydatatypes import *













class self_data_manager(data_manager):
    def __init__(self) -> None:
        super().__init__()
        self._addr_count: int = 0

    def create(self, t: type[generic_data_t]) -> generic_data_t:
        obj = t(data_addr_absolute(self._addr_count, self))
        self._addr_count += t.sizeof()
        return obj
    
    def destroy(self, obj: data_t) -> None:
        obj._addr = data_addr_null()
        pass
        
    def read_value(self, obj: data_t) -> Any:
        obj.addressof().resolve()
        return None

    def write_value(self, obj: data_t, value: Any) -> None:
        obj.addressof().resolve()
        pass












class my_strcut_2(struct_t):
    _aa: u8_t = u8_t
    _bb0: base_bitfield_t[u16_t] = bitfield_(u16_t, 10)
    _bb1: base_bitfield_t[u16_t] = bitfield_(u16_t, 4)
    _bb2: base_bitfield_t[u16_t] = bitfield_(u16_t, 2)
    _cc: u8_t = u8_t
    # _dd: base_array_t[u8_t] = array_(u8_t, 10)
    # _ee: base_ptr_t[u8_t] = ptr_(u8_t)



me = self_data_manager()

aa = me.create(my_strcut_2)
a = aa._aa.read_value()






pass


