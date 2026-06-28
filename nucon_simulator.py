#!/usr/bin/env python3
"""
NUCON Simulator - Professional Tkinter Application
A complete IO module simulator with configuration management.
"""

import tkinter as tk
from tkinter import ttk
import json
import copy
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from enum import Enum


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class ModuleType(Enum):
    EMPTY = "Empty"
    DI = "DI"
    DO = "DO"
    AI = "AI"
    AO = "AO"


@dataclass
class ChannelConfig:
    """Configuration for a single channel (0-31)"""
    process_low: float = 0.0
    process_high: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelConfig':
        return cls(**data)


@dataclass
class DIModuleConfig:
    """DI Module configuration"""
    fail_safe_enabled: bool = False
    fail_safe_value: int = 0
    channels: List[ChannelConfig] = field(default_factory=lambda: [ChannelConfig() for _ in range(32)])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fail_safe_enabled': self.fail_safe_enabled,
            'fail_safe_value': self.fail_safe_value,
            'channels': [ch.to_dict() for ch in self.channels]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DIModuleConfig':
        channels = [ChannelConfig.from_dict(ch) for ch in data.get('channels', [ChannelConfig() for _ in range(32)])]
        return cls(
            fail_safe_enabled=data.get('fail_safe_enabled', False),
            fail_safe_value=data.get('fail_safe_value', 0),
            channels=channels
        )


@dataclass
class DOModuleConfig:
    """DO Module configuration"""
    fail_safe_enabled: bool = False
    fail_safe_value: int = 0
    wdt_timeout: int = 1000
    channels: List[ChannelConfig] = field(default_factory=lambda: [ChannelConfig() for _ in range(32)])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fail_safe_enabled': self.fail_safe_enabled,
            'fail_safe_value': self.fail_safe_value,
            'wdt_timeout': self.wdt_timeout,
            'channels': [ch.to_dict() for ch in self.channels]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DOModuleConfig':
        channels = [ChannelConfig.from_dict(ch) for ch in data.get('channels', [ChannelConfig() for _ in range(32)])]
        return cls(
            fail_safe_enabled=data.get('fail_safe_enabled', False),
            fail_safe_value=data.get('fail_safe_value', 0),
            wdt_timeout=data.get('wdt_timeout', 1000),
            channels=channels
        )


@dataclass
class AIModuleConfig:
    """AI Module configuration"""
    voltage_range: str = "0-10V"
    channels: List[ChannelConfig] = field(default_factory=lambda: [ChannelConfig() for _ in range(32)])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'voltage_range': self.voltage_range,
            'channels': [ch.to_dict() for ch in self.channels]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIModuleConfig':
        channels = [ChannelConfig.from_dict(ch) for ch in data.get('channels', [ChannelConfig() for _ in range(32)])]
        return cls(
            voltage_range=data.get('voltage_range', '0-10V'),
            channels=channels
        )


@dataclass
class AOModuleConfig:
    """AO Module configuration"""
    current_range: str = "0-20mA"
    channels: List[ChannelConfig] = field(default_factory=lambda: [ChannelConfig() for _ in range(32)])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_range': self.current_range,
            'channels': [ch.to_dict() for ch in self.channels]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AOModuleConfig':
        channels = [ChannelConfig.from_dict(ch) for ch in data.get('channels', [ChannelConfig() for _ in range(32)])]
        return cls(
            current_range=data.get('current_range', '0-20mA'),
            channels=channels
        )


@dataclass
class SlotConfig:
    """Configuration for a single slot"""
    module_type: str = ModuleType.EMPTY.value
    module_config: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'module_type': self.module_type,
            'module_config': self.module_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SlotConfig':
        return cls(
            module_type=data.get('module_type', ModuleType.EMPTY.value),
            module_config=data.get('module_config')
        )


@dataclass
class NodeConfig:
    """Configuration for a single node with 14 slots"""
    node_id: int
    slots: List[SlotConfig] = field(default_factory=lambda: [SlotConfig() for _ in range(14)])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'slots': [s.to_dict() for s in self.slots]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeConfig':
        slots = [SlotConfig.from_dict(s) for s in data.get('slots', [SlotConfig() for _ in range(14)])]
        return cls(
            node_id=data.get('node_id', 0),
            slots=slots
        )


@dataclass
class SimulatorData:
    """Root data structure for the entire simulator"""
    nodes: Dict[int, NodeConfig] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodes': {str(k): v.to_dict() for k, v in self.nodes.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulatorData':
        nodes = {
            int(k): NodeConfig.from_dict(v)
            for k, v in data.get('nodes', {}).items()
        }
        return cls(nodes=nodes)


# ============================================================================
# CONFIGURATION WINDOWS
# ============================================================================

class ChannelFrame(ttk.Frame):
    """Frame for editing a single channel configuration"""

    def __init__(self, parent, channel_num: int, config: ChannelConfig, **kwargs):
        super().__init__(parent, **kwargs)
        self.channel_num = channel_num
        self.config = config

        # Channel label
        label = ttk.Label(self, text=f"Channel {channel_num}")
        label.grid(row=0, column=0, sticky='w', padx=5, pady=5)

        # Process Low
        ttk.Label(self, text="Process Low:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.low_entry = ttk.Entry(self, width=10)
        self.low_entry.insert(0, str(config.process_low))
        self.low_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)

        # Process High
        ttk.Label(self, text="Process High:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.high_entry = ttk.Entry(self, width=10)
        self.high_entry.insert(0, str(config.process_high))
        self.high_entry.grid(row=2, column=1, sticky='w', padx=5, pady=2)

    def get_config(self) -> ChannelConfig:
        """Retrieve updated configuration"""
        try:
            return ChannelConfig(
                process_low=float(self.low_entry.get()),
                process_high=float(self.high_entry.get())
            )
        except ValueError:
            return self.config


class DIConfigWindow(tk.Toplevel):
    """Configuration window for DI modules"""

    def __init__(self, parent, slot_name: str, config: DIModuleConfig):
        super().__init__(parent)
        self.title(f"DI Configuration - {slot_name}")
        self.geometry("600x700")
        self.config_data = copy.deepcopy(config)
        self.result = None

        # Create notebook for organization
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Main settings tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Settings")

        ttk.Label(main_frame, text="Fail Safe Configuration:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.fail_safe_var = tk.BooleanVar(value=self.config_data.fail_safe_enabled)
        ttk.Checkbutton(main_frame, variable=self.fail_safe_var).grid(row=0, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(main_frame, text="Fail Safe Value:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.fail_safe_value_entry = ttk.Entry(main_frame, width=15)
        self.fail_safe_value_entry.insert(0, str(self.config_data.fail_safe_value))
        self.fail_safe_value_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # Channels tab with scrollbar
        channels_frame = ttk.Frame(notebook)
        notebook.add(channels_frame, text="Channels")

        canvas = tk.Canvas(channels_frame)
        scrollbar = ttk.Scrollbar(channels_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.channel_frames = []
        for i in range(32):
            cf = ChannelFrame(scrollable_frame, i, self.config_data.channels[i])
            cf.pack(fill='x', padx=5, pady=2)
            self.channel_frames.append(cf)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side='right', padx=2)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right', padx=2)

    def save_config(self):
        """Save the configuration"""
        try:
            self.config_data.fail_safe_enabled = self.fail_safe_var.get()
            self.config_data.fail_safe_value = int(self.fail_safe_value_entry.get())
            self.config_data.channels = [cf.get_config() for cf in self.channel_frames]
            self.result = self.config_data
            self.destroy()
        except ValueError:
            pass

    def cancel(self):
        """Cancel without saving"""
        self.destroy()


class DOConfigWindow(tk.Toplevel):
    """Configuration window for DO modules"""

    def __init__(self, parent, slot_name: str, config: DOModuleConfig):
        super().__init__(parent)
        self.title(f"DO Configuration - {slot_name}")
        self.geometry("600x750")
        self.config_data = copy.deepcopy(config)
        self.result = None

        # Create notebook for organization
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Main settings tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Settings")

        ttk.Label(main_frame, text="Fail Safe Configuration:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.fail_safe_var = tk.BooleanVar(value=self.config_data.fail_safe_enabled)
        ttk.Checkbutton(main_frame, variable=self.fail_safe_var).grid(row=0, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(main_frame, text="Fail Safe Value:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.fail_safe_value_entry = ttk.Entry(main_frame, width=15)
        self.fail_safe_value_entry.insert(0, str(self.config_data.fail_safe_value))
        self.fail_safe_value_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(main_frame, text="WDT Timeout (ms):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.wdt_timeout_entry = ttk.Entry(main_frame, width=15)
        self.wdt_timeout_entry.insert(0, str(self.config_data.wdt_timeout))
        self.wdt_timeout_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # Channels tab with scrollbar
        channels_frame = ttk.Frame(notebook)
        notebook.add(channels_frame, text="Channels")

        canvas = tk.Canvas(channels_frame)
        scrollbar = ttk.Scrollbar(channels_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.channel_frames = []
        for i in range(32):
            cf = ChannelFrame(scrollable_frame, i, self.config_data.channels[i])
            cf.pack(fill='x', padx=5, pady=2)
            self.channel_frames.append(cf)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side='right', padx=2)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right', padx=2)

    def save_config(self):
        """Save the configuration"""
        try:
            self.config_data.fail_safe_enabled = self.fail_safe_var.get()
            self.config_data.fail_safe_value = int(self.fail_safe_value_entry.get())
            self.config_data.wdt_timeout = int(self.wdt_timeout_entry.get())
            self.config_data.channels = [cf.get_config() for cf in self.channel_frames]
            self.result = self.config_data
            self.destroy()
        except ValueError:
            pass

    def cancel(self):
        """Cancel without saving"""
        self.destroy()


class AIConfigWindow(tk.Toplevel):
    """Configuration window for AI modules"""

    def __init__(self, parent, slot_name: str, config: AIModuleConfig):
        super().__init__(parent)
        self.title(f"AI Configuration - {slot_name}")
        self.geometry("600x700")
        self.config_data = copy.deepcopy(config)
        self.result = None

        # Create notebook for organization
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Main settings tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Settings")

        ttk.Label(main_frame, text="Voltage Range:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.voltage_var = tk.StringVar(value=self.config_data.voltage_range)
        voltage_combo = ttk.Combobox(
            main_frame,
            textvariable=self.voltage_var,
            values=["0-10V", "0-5V", "4-20mA", "-10-10V"],
            state="readonly"
        )
        voltage_combo.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # Channels tab with scrollbar
        channels_frame = ttk.Frame(notebook)
        notebook.add(channels_frame, text="Channels")

        canvas = tk.Canvas(channels_frame)
        scrollbar = ttk.Scrollbar(channels_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.channel_frames = []
        for i in range(32):
            cf = ChannelFrame(scrollable_frame, i, self.config_data.channels[i])
            cf.pack(fill='x', padx=5, pady=2)
            self.channel_frames.append(cf)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side='right', padx=2)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right', padx=2)

    def save_config(self):
        """Save the configuration"""
        try:
            self.config_data.voltage_range = self.voltage_var.get()
            self.config_data.channels = [cf.get_config() for cf in self.channel_frames]
            self.result = self.config_data
            self.destroy()
        except ValueError:
            pass

    def cancel(self):
        """Cancel without saving"""
        self.destroy()


class AOConfigWindow(tk.Toplevel):
    """Configuration window for AO modules"""

    def __init__(self, parent, slot_name: str, config: AOModuleConfig):
        super().__init__(parent)
        self.title(f"AO Configuration - {slot_name}")
        self.geometry("600x700")
        self.config_data = copy.deepcopy(config)
        self.result = None

        # Create notebook for organization
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Main settings tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Settings")

        ttk.Label(main_frame, text="Current Range:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.current_var = tk.StringVar(value=self.config_data.current_range)
        current_combo = ttk.Combobox(
            main_frame,
            textvariable=self.current_var,
            values=["0-20mA", "0-10mA", "0-10V", "4-20mA"],
            state="readonly"
        )
        current_combo.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # Channels tab with scrollbar
        channels_frame = ttk.Frame(notebook)
        notebook.add(channels_frame, text="Channels")

        canvas = tk.Canvas(channels_frame)
        scrollbar = ttk.Scrollbar(channels_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.channel_frames = []
        for i in range(32):
            cf = ChannelFrame(scrollable_frame, i, self.config_data.channels[i])
            cf.pack(fill='x', padx=5, pady=2)
            self.channel_frames.append(cf)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side='right', padx=2)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='right', padx=2)

    def save_config(self):
        """Save the configuration"""
        try:
            self.config_data.current_range = self.current_var.get()
            self.config_data.channels = [cf.get_config() for cf in self.channel_frames]
            self.result = self.config_data
            self.destroy()
        except ValueError:
            pass

    def cancel(self):
        """Cancel without saving"""
        self.destroy()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class NUCONSimulator:
    """Main application controller"""

    def __init__(self, root):
        self.root = root
        self.root.title("NUCON Simulator")
        self.root.geometry("900x600")

        # Data model
        self.data = SimulatorData()

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        # Create main UI
        self.setup_ui()

        # Store for opened config windows
        self.config_windows: Dict[str, tk.Toplevel] = {}

    def setup_ui(self):
        """Setup the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Left side - Tree
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(side='left', fill='both', expand=True)

        ttk.Label(tree_frame, text="IO Simulator", font=('Arial', 12, 'bold')).pack(anchor='w', pady=5)

        # Treeview with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side='right', fill='y')

        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            height=25
        )
        tree_scroll.config(command=self.tree.yview)
        self.tree.pack(side='left', fill='both', expand=True)

        # Add root item
        self.root_item = self.tree.insert('', 'end', text='IO Simulator', open=True)

        # Bind events
        self.tree.bind('<Button-3>', self.on_tree_right_click)
        self.tree.bind('<Button-1>', self.on_tree_left_click)

        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)

    def get_next_node_id(self) -> int:
        """Get the smallest available node ID"""
        if not self.data.nodes:
            return 1
        return max(self.data.nodes.keys()) + 1

    def add_node(self):
        """Add a new IO Node"""
        node_id = self.get_next_node_id()
        node = NodeConfig(node_id=node_id)
        self.data.nodes[node_id] = node
        self.refresh_tree()

    def copy_node(self, node_id: int):
        """Copy a node with all its configurations"""
        if node_id not in self.data.nodes:
            return

        source_node = self.data.nodes[node_id]
        new_id = self.get_next_node_id()
        new_node = NodeConfig(
            node_id=new_id,
            slots=[copy.deepcopy(slot) for slot in source_node.slots]
        )
        self.data.nodes[new_id] = new_node
        self.refresh_tree()

    def delete_node(self, node_id: int):
        """Delete a node"""
        if node_id in self.data.nodes:
            del self.data.nodes[node_id]
            self.refresh_tree()

    def add_module_to_slot(self, node_id: int, slot_num: int, module_type: str):
        """Add a module to a slot"""
        if node_id not in self.data.nodes:
            return

        node = self.data.nodes[node_id]
        slot = node.slots[slot_num]

        # Initialize module config based on type
        if module_type == ModuleType.DI.value:
            slot.module_config = DIModuleConfig().to_dict()
        elif module_type == ModuleType.DO.value:
            slot.module_config = DOModuleConfig().to_dict()
        elif module_type == ModuleType.AI.value:
            slot.module_config = AIModuleConfig().to_dict()
        elif module_type == ModuleType.AO.value:
            slot.module_config = AOModuleConfig().to_dict()

        slot.module_type = module_type
        self.refresh_tree()

    def delete_module(self, node_id: int, slot_num: int):
        """Delete a module from a slot"""
        if node_id not in self.data.nodes:
            return

        node = self.data.nodes[node_id]
        slot = node.slots[slot_num]
        slot.module_type = ModuleType.EMPTY.value
        slot.module_config = None
        self.refresh_tree()

    def refresh_tree(self):
        """Refresh the tree view"""
        # Clear existing items except root
        for item in self.tree.get_children(self.root_item):
            self.tree.delete(item)

        # Add nodes
        for node_id in sorted(self.data.nodes.keys()):
            node = self.data.nodes[node_id]
            node_item = self.tree.insert(self.root_item, 'end', text=f'Node{node_id}', open=True)

            # Add all 14 slots
            for slot_num in range(14):
                slot = node.slots[slot_num]
                slot_text = f"Slot{slot_num + 1}-{slot.module_type}"
                slot_item = self.tree.insert(node_item, 'end', text=slot_text)

                # Store metadata for easy access
                self.tree.set(slot_item, '#0', slot_text)

    def on_tree_right_click(self, event):
        """Handle right-click on tree"""
        item = self.tree.identify('item', event.x, event.y)

        if not item:
            return

        # Determine what was clicked
        text = self.tree.item(item, 'text')
        parent = self.tree.parent(item)

        self.context_menu.delete(0, 'end')

        if item == self.root_item:
            # Clicked on root
            self.context_menu.add_command(label="Add IO Node", command=self.add_node)

        elif parent == self.root_item:
            # Clicked on a Node
            node_id = int(text.replace('Node', ''))
            self.context_menu.add_command(
                label="Copy Node",
                command=lambda: self.copy_node(node_id)
            )
            self.context_menu.add_command(
                label="Delete Node",
                command=lambda: self.delete_node(node_id)
            )

        elif self.tree.parent(parent) == self.root_item:
            # Clicked on a Slot
            node_id = int(self.tree.item(parent, 'text').replace('Node', ''))
            slot_num = int(text.split('-')[0].replace('Slot', '')) - 1

            self.context_menu.add_command(
                label="Add Module",
                command=lambda: self.show_add_module_menu(node_id, slot_num, event)
            )
            if node_id in self.data.nodes and self.data.nodes[node_id].slots[slot_num].module_type != ModuleType.EMPTY.value:
                self.context_menu.add_command(
                    label="Delete Module",
                    command=lambda: self.delete_module(node_id, slot_num)
                )

        if self.context_menu.index('end') is not None:
            self.context_menu.post(event.x_root, event.y_root)

    def show_add_module_menu(self, node_id: int, slot_num: int, event):
        """Show submenu for adding modules"""
        module_menu = tk.Menu(self.context_menu, tearoff=0)

        for module_type in [ModuleType.DI, ModuleType.DO, ModuleType.AI, ModuleType.AO]:
            module_menu.add_command(
                label=module_type.value,
                command=lambda mt=module_type.value: self.add_module_to_slot(node_id, slot_num, mt)
            )

        # Display submenu
        self.context_menu.add_cascade(label="Select Module", menu=module_menu)
        self.context_menu.post(event.x_root, event.y_root)

    def on_tree_left_click(self, event):
        """Handle left-click on tree"""
        item = self.tree.identify('item', event.x, event.y)

        if not item:
            return

        text = self.tree.item(item, 'text')
        parent = self.tree.parent(item)

        # Check if clicked on a slot
        if self.tree.parent(parent) == self.root_item:
            node_id = int(self.tree.item(parent, 'text').replace('Node', ''))
            slot_num = int(text.split('-')[0].replace('Slot', '')) - 1

            if node_id in self.data.nodes:
                slot = self.data.nodes[node_id].slots[slot_num]
                if slot.module_type != ModuleType.EMPTY.value:
                    self.open_config_window(node_id, slot_num, slot)

    def open_config_window(self, node_id: int, slot_num: int, slot: SlotConfig):
        """Open the configuration window for a slot"""
        slot_name = f"Node{node_id}-Slot{slot_num + 1}"

        if slot.module_type == ModuleType.DI.value:
            config = DIModuleConfig.from_dict(slot.module_config) if slot.module_config else DIModuleConfig()
            window = DIConfigWindow(self.root, slot_name, config)
        elif slot.module_type == ModuleType.DO.value:
            config = DOModuleConfig.from_dict(slot.module_config) if slot.module_config else DOModuleConfig()
            window = DOConfigWindow(self.root, slot_name, config)
        elif slot.module_type == ModuleType.AI.value:
            config = AIModuleConfig.from_dict(slot.module_config) if slot.module_config else AIModuleConfig()
            window = AIConfigWindow(self.root, slot_name, config)
        elif slot.module_type == ModuleType.AO.value:
            config = AOModuleConfig.from_dict(slot.module_config) if slot.module_config else AOModuleConfig()
            window = AOConfigWindow(self.root, slot_name, config)
        else:
            return

        # Store reference
        self.config_windows[slot_name] = window

        # Wait for window to close and save result
        self.root.wait_window(window)
        if hasattr(window, 'result') and window.result:
            slot.module_config = window.result.to_dict()
            self.refresh_tree()

        # Remove reference
        if slot_name in self.config_windows:
            del self.config_windows[slot_name]


def main():
    """Main entry point"""
    root = tk.Tk()
    app = NUCONSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
