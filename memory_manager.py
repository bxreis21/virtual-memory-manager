
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
        self.tlb = [None, None]

        self.physical_memory_pages_initial_addresses = [
            0 << 12,
            1 << 12,
            2 << 12,
            3 << 12,
        ]

        self.history = []

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

        return self.page_table[page]
                

    def get_page_from_secondary(self, page):
        self.update_page_table(page)
        memory_address = self.page_table[page]

        page_from_secondary = self.secondary_memory.access_frame(page)

        # print("pfs:", type(page_from_secondary))
        #print("pfs len:", len(page_from_secondary.keys()))

        self.physical_memory.save_page(memory_address, page_from_secondary)

        print()
        print("memory page allocated:", self.page_table[page] // 4096)
        print("page in:", page)
        


    def start_simulation(self):

        print("#######################################################################")
        print("------------------ virtual memory manager simulation ------------------")
        print("#######################################################################")

        for index, address in enumerate(self.logic_addresses):

            current_address_page = self.get_page(address)
            current_address_shift = self.get_shifting(address)

            print()
            print(f"------------------------ {index} ------------------------")
            print()
            print("address: ", address)
            print("page: ", current_address_page)
            print("shift: ", current_address_shift)

            if self.page_table[current_address_page] != None:
                print("in memory")
                print("memory address: ", self.page_table[current_address_page] + current_address_shift)
                print("value: ", self.physical_memory.access(self.page_table[current_address_page] + current_address_shift))

            else:
                print()
                print("out of memory")
                self.get_page_from_secondary(current_address_page)
                print("memory address: ", self.page_table[current_address_page] + current_address_shift)
                print("value: ", self.physical_memory.access(self.page_table[current_address_page] + current_address_shift))

        print()
        print(f"---------------------- END ----------------------")
        
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
