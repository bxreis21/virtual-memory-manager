
class Secondary_Memory:

    def __init__(self, path):
        self.path = path

    def access_frame(self, frame):
        with open(self.path, 'rb') as f:
            f.seek(frame)
            frame_data = dict()
            initial_frame_address = frame * (1<<12)
            final_frame_address = initial_frame_address + (1 <<12)

            for index, address in enumerate(range(initial_frame_address, final_frame_address)):
                frame_data[index] = f.read(1)

            print(f"address range of the contents accessed in secondary memory: {initial_frame_address} - {final_frame_address}")

            return frame_data
        
class Physical_Memory:

    def __init__(self):
        self.memory = dict()

    def access(self, address):
        return self.memory[address]

    def save_page(self, address, page_data):
        initial_page_address = address
        final_page_address = initial_page_address + (1 <<12)

        for index, address in enumerate(range(initial_page_address , final_page_address)):
            if address in self.memory.keys(): raise IndexError("the data has been corrupted")
            self.memory[address] = page_data[index]

        print(f"changed memory block: {initial_page_address} - {final_page_address}")

    def clear_page(self, address):
        initial_page_address = address
        final_page_address = initial_page_address + (1 <<12)

        for index, address in enumerate(range(initial_page_address , final_page_address)):
            del self.memory[address]

class Memory_Manager:

    def __init__(self, logic_addresses, secondary_memory_pass):
        self.physical_memory = Physical_Memory()
        self.secondary_memory = Secondary_Memory(secondary_memory_pass)
        self.logic_addresses = logic_addresses

        self.page_table = [None] * 16
        self.tlb = [] # lista para TLB

        self.physical_memory_pages_initial_addresses = [
            0 << 12,
            1 << 12,
            2 << 12,
            3 << 12,
        ]

        self.history = [] # Política FIFO

        # Estatísticas
        self.total_addresses = 0
        self.page_faults = 0
        self.tlb_hits = 0

    @staticmethod
    def get_page(address):
        return address >> 12
    
    @staticmethod
    def get_shifting(address):
        return address & 0x0FFF
    
    def update_page_table(self, page):
        busy_pages = sum(1 for item in self.page_table if item is not None)
        self.history.insert(0, page)

        if busy_pages < 4:
            self.page_table[page] = self.physical_memory_pages_initial_addresses[busy_pages]          

        else:
            page_out = self.history.pop()
            print("page out:", page_out)

            memory_page_now_free = self.page_table[page_out]
            print("memory free page:", memory_page_now_free // 4096)
            print("memory free page initial address:", memory_page_now_free)

            self.physical_memory.clear_page(memory_page_now_free)
            self.page_table[page] = memory_page_now_free
            self.page_table[page_out] = None

            # atualizar TLB
            self.tlb = [entry for entry in self.tlb if entry[0] != page_out]

        return self.page_table[page]
                

    def get_page_from_secondary(self, page):
        self.page_faults += 1 # contabilizar page fault

        frame_address = self.update_page_table(page)

        page_from_secondary = self.secondary_memory.access_frame(page)

        self.physical_memory.save_page(frame_address, page_from_secondary)

        print()
        print("page fault - Loaded page:", page)
        print("memory page allocated:", frame_address // 4096)
        #print("page in:", page)

        # atualiza TLB (FIFO)
        if len(self.tlb) >= 2:
            removed = self.tlb.pop(0)
            print(f"TLB FULL. Removed entry: page {removed[0]}")
        
        self.tlb.append((page, frame_address))
        

    def check_tlb(self, page):
        # verifica se a página está na TLB e retorna frame_address se encontrar
        for p, frame_addr in self.tlb:
            if p == page:
                return frame_addr
        return None

    def start_simulation(self):

        print("#######################################################################")
        print("------------------ virtual memory manager simulation ------------------")
        print("#######################################################################")

        for index, address in enumerate(self.logic_addresses):

            self.total_addresses += 1

            current_address_page = self.get_page(address)
            current_address_shift = self.get_shifting(address)

            print()
            print(f"------------------------ {index} ------------------------")
            print()
            print("address: ", address)
            print("page: ", current_address_page)
            print("shift: ", current_address_shift)

            frame_address = self.check_tlb(current_address_page)
            if frame_address is not None:
                self.tlb_hits += 1
                print("TLB HIT")
                physical_address = frame_address + current_address_shift
                print("physical address:", physical_address)
                value_byte = self.physical_memory.access(physical_address)
                print("value:", value_byte[0]) # valor o inteiro do byte armazenado no endereço

            else:
                print("TLB MISS")
                if self.page_table[current_address_page] is not None:
                    # página não está na TLB. Atualizar TLB
                    frame_address = self.page_table[current_address_page]
                    print("in memory")
                    physical_address = frame_address + current_address_shift
                    print("physical address:", physical_address)
                    value_byte = self.physical_memory.access(physical_address)
                    print("value:", value_byte[0]) # valor o inteiro do byte armazenado no endereço

                    # atualizar TLB
                    if len(self.tlb) >= 2:
                        removed = self.tlb.pop(0)
                        print(f"TLB full. Removed entry: page {removed[0]}")

                    self.tlb.append((current_address_page, frame_address))

                else:
                    # page fault
                    print("page fault - page not in memory...loading from secondary memory")
                    self.get_page_from_secondary(current_address_page)
                    frame_address = self.page_table[current_address_page]
                    physical_address = frame_address + current_address_shift
                    print("physical address:", physical_address)
                    value_byte = self.physical_memory.access(physical_address)
                    print("value:", value_byte[0]) # valor o inteiro do byte armazenado no endereço


        print()
        print(f"---------------------- END ----------------------")
        print(f"Total addresses translated: {self.total_addresses}")
        print(f"Page fault rate: {(self.page_faults / self.total_addresses)*100:.2f}%")
        print(f"TLB hit rate: {(self.tlb_hits / self.total_addresses)*100:.2f}%")

if __name__ == "__main__":

    SECONDARY_MEMORY_PATH = 'BACKING_STORE.bin'

    LOGIC_ADDRESSES = [
        0b0001000011111111,
        0b0001111100000000,
        0b0010111100000000,
        0b0010000011111111,
        0b0100111100000000,
        0b0100000011111111,
        0b1000111100000000,
        0b1000000011111111,
        0b1001111100000000,
        0b1001000011111111,
        0b1010111100000000,
        0b1010000011111111,
        0b1011111100000000,
        0b1011000011111111,
        0b1111111100000000,
        0b1111000011111111,
    ]

    memory_manager = Memory_Manager(LOGIC_ADDRESSES, SECONDARY_MEMORY_PATH)
    memory_manager.start_simulation()
