#
# This file is part of LiteX (Adapted from Migen for LiteX usage).
#
# This file is Copyright (c) 2013-2014 Sebastien Bourdeauducq <sb@m-labs.hk>
# This file is Copyright (c) 2013-2023 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2013-2017 Robert Jordens <jordens@gmail.com>
# This file is Copyright (c) 2016-2018 whitequark <whitequark@whitequark.org>
# This file is Copyright (c) 2017 Adam Greig <adam@adamgreig.com>
# This file is Copyright (c) 2016 Ben Reynwar <ben@reynwar.net>
# This file is Copyright (c) 2018 David Craven <david@craven.ch>
# This file is Copyright (c) 2015 Guy Hutchison <ghutchis@gmail.com>
# This file is Copyright (c) 2013 Nina Engelhardt <nina.engelhardt@omnium-gatherum.de>
# This file is Copyright (c) 2018 Robin Ole Heinemann <robin.ole.heinemann@t-online.de>
# SPDX-License-Identifier: BSD-2-Clause

import time
import datetime
import collections

from enum import IntEnum
from operator import itemgetter

from migen.fhdl.structure   import *
from migen.fhdl.structure   import _Operator, _Slice, _Assign, _Fragment
from migen.fhdl.tools       import *
from migen.fhdl.tools       import _apply_lowerer, _Lowerer
from migen.fhdl.conv_output import ConvOutput
from migen.fhdl.specials    import Instance, Memory

from litex.gen import LiteXContext
from litex.gen.fhdl.expression import _generate_expression, _generate_signal
from litex.gen.fhdl.namer      import build_signal_namespace
from litex.gen.fhdl.hierarchy  import LiteXHierarchyExplorer

from litex.build.tools import get_litex_git_revision

# ------------------------------------------------------------------------------------------------ #
#                                     BANNER/TRAILER/SEPARATORS                                    #
# ------------------------------------------------------------------------------------------------ #

_tab = " "*4

def _generate_banner(filename, device):
    return """\
// -----------------------------------------------------------------------------
// Auto-Generated by:        __   _ __      _  __
//                          / /  (_) /____ | |/_/
//                         / /__/ / __/ -_)>  <
//                        /____/_/\\__/\\__/_/|_|
//                     Build your hardware, easily!
//                   https://github.com/enjoy-digital/litex
//
// Filename   : {filename}.v
// Device     : {device}
// LiteX sha1 : {revision}
// Date       : {date}
//------------------------------------------------------------------------------\n
""".format(
    device   = device,
    filename = filename,
    revision = get_litex_git_revision(),
    date     = datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
)

def _generate_trailer():
    return """
// -----------------------------------------------------------------------------
//  Auto-Generated by LiteX on {date}.
//------------------------------------------------------------------------------
""".format(
    date=datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
)

def _generate_separator(msg=""):
    r =  "\n"
    r +=  "//" + "-"*78 + "\n"
    r += f"// {msg}\n"
    r +=  "//" + "-"*78 + "\n"
    r += "\n"
    return r

# ------------------------------------------------------------------------------------------------ #
#                                         TIMESCALE                                                #
# ------------------------------------------------------------------------------------------------ #

def _generate_timescale(time_unit="1ns", time_precision="1ps"):
    r = f"`timescale {time_unit} / {time_precision}\n"
    return r

# ------------------------------------------------------------------------------------------------ #
#                                         HIERARCHY                                                #
# ------------------------------------------------------------------------------------------------ #

def _generate_hierarchy(top):
    if top is None:
        return ""
    else:
        hierarchy_explorer = LiteXHierarchyExplorer(top=top, depth=None, with_colors=False)
        r = "/*\n"
        for l in hierarchy_explorer.get_hierarchy().split("\n"):
            r += l + "\n"
        r = r[:-1]
        r += "*/\n"
        return r

# ------------------------------------------------------------------------------------------------ #
#                                    RESERVED KEYWORDS                                             #
# ------------------------------------------------------------------------------------------------ #

_ieee_1800_2017_verilog_reserved_keywords = {
     "accept_on",          "alias",          "always",         "always_comb",          "always_ff",
  "always_latch",            "and",          "assert",              "assign",             "assume",
     "automatic",         "before",           "begin",                "bind",               "bins",
        "binsof",            "bit",           "break",                 "buf",             "bufif0",
        "bufif1",           "byte",            "case",               "casex",              "casez",
          "cell",        "chandle",         "checker",               "class",           "clocking",
          "cmos",         "config",           "const",          "constraint",            "context",
      "continue",          "cover",      "covergroup",          "coverpoint",              "cross",
      "deassign",        "default",        "defparam",              "design",            "disable",
          "dist",             "do",            "edge",                "else",                "end",
       "endcase",     "endchecker",        "endclass",         "endclocking",          "endconfig",
   "endfunction",    "endgenerate",        "endgroup",        "endinterface",          "endmodule",
    "endpackage",   "endprimitive",      "endprogram",         "endproperty",        "endsequence",
    "endspecify",       "endtable",         "endtask",                "enum",              "event",
    "eventually",         "expect",          "export",             "extends",             "extern",
         "final",    "first_match",             "for",               "force",            "foreach",
       "forever",           "fork",        "forkjoin",            "function",           "generate",
        "genvar",         "global",          "highz0",              "highz1",                 "if",
           "iff",         "ifnone",     "ignore_bins",        "illegal_bins",         "implements",
       "implies",         "import",          "incdir",             "include",            "initial",
         "inout",          "input",          "inside",            "instance",                "int",
       "integer",   "interconnect",       "interface",           "intersect",               "join",
      "join_any",      "join_none",           "large",                 "let",            "liblist",
       "library",          "local",      "localparam",               "logic",            "longint",
   "macromodule",        "matches",          "medium",             "modport",             "module",
          "nand",        "negedge",         "nettype",                 "new",           "nexttime",
          "nmos",            "nor", "noshowcancelled",                 "not",             "notif0",
        "notif1",           "null",              "or",              "output",            "package",
        "packed",      "parameter",            "pmos",             "posedge",          "primitive",
      "priority",        "program",        "property",           "protected",              "pull0",
         "pull1",       "pulldown",          "pullup", "pulsestyle_ondetect", "pulsestyle_onevent",
          "pure",           "rand",           "randc",            "randcase",       "randsequence",
         "rcmos",           "real",        "realtime",                 "ref",                "reg",
     "reject_on",        "release",    "      repeat",            "restrict",             "return",
         "rnmos",          "rpmos",           "rtran",            "rtranif0",           "rtranif1",
      "s_always",   "s_eventually",      "s_nexttime",             "s_until",       "s_until_with",
      "scalared",       "sequence",        "shortint",           "shortreal",      "showcancelled",
        "signed",          "small",            "soft",               "solve",            "specify",
     "specparam",         "static",          "string",              "strong",            "strong0",
       "strong1",         "struct",           "super",             "supply0",            "supply1",
"sync_accept_on", "sync_reject_on",           "table",              "tagged",               "task",
          "this",     "throughout",            "time",       "timeprecision",           "timeunit",
          "tran",        "tranif0",         "tranif1",                 "tri",               "tri0",
          "tri1",         "triand",           "trior",              "trireg",               "type",
       "typedef",   "       union",          "unique",             "unique0",           "unsigned",
         "until",     "until_with",         "untyped",                 "use",           "   uwire",
           "var",       "vectored",         "virtual",                "void",               "wait",
    "wait_order",           "wand",            "weak",               "weak0",              "weak1",
         "while",       "wildcard",            "wire",                "with",             "within",
           "wor",           "xnor",             "xor",
}

# ------------------------------------------------------------------------------------------------ #
#                                          NODES                                                   #
# ------------------------------------------------------------------------------------------------ #

class AssignType(IntEnum):
    BLOCKING     = 0
    NON_BLOCKING = 1
    SIGNAL       = 2

def _generate_node(ns, at, level, node, target_filter=None):
    assert at in [item.value for item in AssignType]
    if target_filter is not None and target_filter not in list_targets(node):
        return ""

    # Assignment.
    elif isinstance(node, _Assign):
        if at == AssignType.BLOCKING:
            assignment = " = "
        elif at == AssignType.NON_BLOCKING:
            assignment = " <= "
        elif is_variable(node.l):
            assignment = " = "
        else:
            assignment = " <= "
        return _tab*level + _generate_expression(ns, node.l)[0] + assignment + _generate_expression(ns, node.r)[0] + ";\n"

    # Iterable.
    elif isinstance(node, collections.abc.Iterable):
        return "".join(_generate_node(ns, at, level, n, target_filter) for n in node)

    # If.
    elif isinstance(node, If):
        r = _tab*level + "if (" + _generate_expression(ns, node.cond)[0] + ") begin\n"
        r += _generate_node(ns, at, level + 1, node.t, target_filter)
        if node.f:
            r += _tab*level + "end else begin\n"
            r += _generate_node(ns, at, level + 1, node.f, target_filter)
        r += _tab*level + "end\n"
        return r

    # Case.
    elif isinstance(node, Case):
        if node.cases:
            r = _tab*level + "case (" + _generate_expression(ns, node.test)[0] + ")\n"
            css = [(k, v) for k, v in node.cases.items() if isinstance(k, Constant)]
            css = sorted(css, key=lambda x: x[0].value)
            for choice, statements in css:
                r += _tab*(level + 1) + _generate_expression(ns, choice)[0] + ": begin\n"
                r += _generate_node(ns, at, level + 2, statements, target_filter)
                r += _tab*(level + 1) + "end\n"
            if "default" in node.cases:
                r += _tab*(level + 1) + "default: begin\n"
                r += _generate_node(ns, at, level + 2, node.cases["default"], target_filter)
                r += _tab*(level + 1) + "end\n"
            r += _tab*level + "endcase\n"
            return r
        else:
            return ""

    # Display.
    elif isinstance(node, Display):
        s = "\"" + node.s + "\""
        for arg in node.args:
            s += ", "
            if isinstance(arg, Signal):
                s += ns.get_name(arg)
            else:
                s += str(arg)
        return _tab*level + "$display(" + s + ");\n"

    # Finish.
    elif isinstance(node, Finish):
        return _tab*level + "$finish;\n"

    # Unknown.
    else:
        raise TypeError(f"Node of unrecognized type: {str(type(node))}")

# ------------------------------------------------------------------------------------------------ #
#                                        ATTRIBUTES                                                #
# ------------------------------------------------------------------------------------------------ #

def _generate_attribute(attr, attr_translate):
    r = ""
    first = True
    for attr in sorted(attr, key=lambda x: ("", x) if isinstance(x, str) else x):
        if isinstance(attr, tuple):
            # Platform-dependent attribute.
            attr_name, attr_value = attr
        else:
            # Translated attribute.
            at = attr_translate.get(attr, None)
            if at is None:
                continue
            attr_name, attr_value = at
        if not first:
            r += ", "
        first = False
        const_expr = "\"" + attr_value + "\"" if not isinstance(attr_value, int) else str(attr_value)
        r += attr_name + " = " + const_expr
    if r:
        r = "(* " + r + " *)\n"
    return r

# ------------------------------------------------------------------------------------------------ #
#                                           MODULE                                                 #
# ------------------------------------------------------------------------------------------------ #

def _use_wire(stmts):
    return (len(stmts) == 1 and isinstance(stmts[0], _Assign) and
            not isinstance(stmts[0].l, _Slice))

def _list_comb_wires(f):
    r = set()
    groups = group_by_targets(f.comb)
    for g in groups:
        if _use_wire(g[1]):
            r |= g[0]
    return r

def _generate_module(f, ios, name, ns, attr_translate):
    sigs         = list_signals(f) | list_special_ios(f, ins=True, outs=True, inouts=True)
    special_outs = list_special_ios(f, ins=False, outs=True,  inouts=True)
    inouts       = list_special_ios(f, ins=False, outs=False, inouts=True)
    targets      = list_targets(f) | special_outs
    wires        = _list_comb_wires(f) | special_outs

    r = f"module {name} (\n"
    firstp = True
    for sig in sorted(ios, key=lambda x: ns.get_name(x)):
        if not firstp:
            r += ",\n"
        firstp = False
        attr = _generate_attribute(sig.attr, attr_translate)
        if attr:
            r += _tab + attr
        sig.type = "wire"
        sig.name = ns.get_name(sig)
        sig.port = True
        if sig in inouts:
            sig.direction = "inout"
            r += _tab + "inout  wire " + _generate_signal(ns, sig)
        elif sig in targets:
            sig.direction = "output"
            if sig in wires:
                r += _tab + "output wire " + _generate_signal(ns, sig)
            else:
                sig.type = "reg"
                r += _tab + "output reg  " + _generate_signal(ns, sig)
        else:
            sig.direction = "input"
            r += _tab + "input  wire " + _generate_signal(ns, sig)
    r += "\n);\n\n"

    return r

def _generate_signals(f, ios, name, ns, attr_translate, regs_init):
    sigs = list_signals(f) | list_special_ios(f, ins=True, outs=True, inouts=True)
    special_outs = list_special_ios(f, ins=False, outs=True,  inouts=True)
    inouts       = list_special_ios(f, ins=False, outs=False, inouts=True)
    targets      = list_targets(f) | special_outs
    wires        = _list_comb_wires(f) | special_outs

    r = ""
    for sig in sorted(sigs - ios, key=lambda x: ns.get_name(x)):
        r += _generate_attribute(sig.attr, attr_translate)
        if sig in wires:
            r += "wire " + _generate_signal(ns, sig) + ";\n"
        else:
            r += "reg  " + _generate_signal(ns, sig)
            if regs_init:
                r += " = " + _generate_expression(ns, sig.reset)[0]
            r += ";\n"
    return r

# ------------------------------------------------------------------------------------------------ #
#                                  COMBINATORIAL LOGIC                                             #
# ------------------------------------------------------------------------------------------------ #

def _generate_combinatorial_logic_sim(f, ns):
    r = ""
    if f.comb:
        target_stmt_map = collections.defaultdict(list)

        for statement in flat_iteration(f.comb):
            targets = list_targets(statement)
            for t in targets:
                target_stmt_map[t].append(statement)

        groups = group_by_targets(f.comb)

        for n, (t, stmts) in enumerate(target_stmt_map.items()):
            assert isinstance(t, Signal)
            if _use_wire(stmts):
                r += "assign " + _generate_node(ns, AssignType.BLOCKING, 0, stmts[0])
            else:
                r += "always @(*) begin\n"
                r += _tab + ns.get_name(t) + " <= " + _generate_expression(ns, t.reset)[0] + ";\n"
                r += _generate_node(ns, AssignType.NON_BLOCKING, 1, stmts, t)
                r += "end\n"
    r += "\n"
    return r

def _generate_combinatorial_logic_synth(f, ns):
    r = ""
    if f.comb:
        groups = group_by_targets(f.comb)

        for n, g in enumerate(groups):
            if _use_wire(g[1]):
                r += "assign " + _generate_node(ns, AssignType.BLOCKING, 0, g[1][0])
            else:
                r += "always @(*) begin\n"
                for t in sorted(g[0], key=lambda x: ns.get_name(x)):
                    r += _tab + ns.get_name(t) + " <= " + _generate_expression(ns, t.reset)[0] + ";\n"
                r += _generate_node(ns, AssignType.NON_BLOCKING, 1, g[1])
                r += "end\n"
    r += "\n"
    return r

# ------------------------------------------------------------------------------------------------ #
#                                    SYNCHRONOUS LOGIC                                             #
# ------------------------------------------------------------------------------------------------ #

def _generate_synchronous_logic(f, ns):
    r = ""
    for k, v in sorted(f.sync.items(), key=itemgetter(0)):
        r += "always @(posedge " + ns.get_name(f.clock_domains[k].clk) + ") begin\n"
        r += _generate_node(ns, AssignType.SIGNAL, 1, v)
        r += "end\n\n"
    return r

# ------------------------------------------------------------------------------------------------ #
#                                      SPECIALS                                                    #
# ------------------------------------------------------------------------------------------------ #

def _generate_specials(name, overrides, specials, namespace, add_data_file, attr_translate):
    r = ""
    for special in sorted(specials, key=lambda x: x.duid):
        if hasattr(special, "attr"):
            r += _generate_attribute(special.attr, attr_translate)
        # Replace Migen Memory's emit_verilog with LiteX's implementation.
        if isinstance(special, Memory):
            from litex.gen.fhdl.memory import _memory_generate_verilog
            pr = _memory_generate_verilog(name, special, namespace, add_data_file)
        # Replace Migen Instance's emit_verilog with LiteX's implementation.
        elif isinstance(special, Instance):
            from litex.gen.fhdl.instance import _instance_generate_verilog
            pr = _instance_generate_verilog(special, namespace, add_data_file)
        else:
            pr = call_special_classmethod(overrides, special, "emit_verilog", namespace, add_data_file)
        if pr is None:
            raise NotImplementedError("Special " + str(special) + " failed to implement emit_verilog")
        r += pr
    return r

# ------------------------------------------------------------------------------------------------ #
#                                       LOWERER                                                    #
# ------------------------------------------------------------------------------------------------ #

def _lower_slice_cat(node, start, length):
    while isinstance(node, Cat):
        cat_start = 0
        for e in node.l:
            if cat_start <= start < cat_start + len(e) >= start + length:
                start -= cat_start
                node = e
                break
            cat_start += len(e)
        else:
            break
    return node, start

def _lower_slice_replicate(node, start, length):
    while isinstance(node, Replicate):
        if start//len(node.v) == (start + length - 1)//len(node.v):
            start = start % len(node.v)
            node = node.v
        else:
            break
    return node, start

class _ComplexSliceLowerer(_Lowerer):
    def visit_Slice(self, node):
        length = len(node)
        start = 0
        while isinstance(node, _Slice):
            start += node.start
            node = node.value
            while True:
                node, start = _lower_slice_cat(node, start, length)
                former_node = node
                node, start = _lower_slice_replicate(node, start, length)
                if node is former_node:
                    break
        if start == 0 and len(node) == length:
            return NodeTransformer.visit(self, node)
        if isinstance(node, Signal):
            node = _Slice(node, start, start + length)
        else:
            slice_proxy = Signal(value_bits_sign(node))
            if self.target_context:
                a = _Assign(node, slice_proxy)
            else:
                a = _Assign(slice_proxy, node)
            self.comb.append(self.visit_Assign(a))
            node = _Slice(slice_proxy, start, start + length)
        return NodeTransformer.visit_Slice(self, node)

def lower_complex_slices(f):
    return _apply_lowerer(_ComplexSliceLowerer(), f)

# ------------------------------------------------------------------------------------------------ #
#                                    FHDL --> VERILOG                                              #
# ------------------------------------------------------------------------------------------------ #

class DummyAttrTranslate(dict):
    def __getitem__(self, k):
        return (k, "true")

def convert(f, ios=set(), name="top", platform=None,
    # Verilog parameters.
    special_overrides = dict(),
    attr_translate    = DummyAttrTranslate(),
    regular_comb      = True,
    regs_init         = True,
    # Sim parameters.
    time_unit      = "1ns",
    time_precision = "1ps",
    ):

    # Build Logic.
    # ------------

    # Create ConvOutput.
    r = ConvOutput()

    # Convert to FHDL's fragments is not already done.
    if not isinstance(f, _Fragment):
        f = f.get_fragment()

    # Verify/Create Clock Domains.
    for cd_name in sorted(list_clock_domains(f)):
        # Try to get Clock Domain.
        try:
            f.clock_domains[cd_name]
        # If not found, raise Error.
        except:
            msg = f"""Unresolved clock domain {cd_name}, availables:\n"""
            for f in f.clock_domains:
                msg += f"- {f.name}\n"
            raise Exception(msg)

    # Lower complex slices.
    f = lower_complex_slices(f)

    # Insert resets.
    insert_resets(f)

    # Lower basics.
    f = lower_basics(f)

    # Lower specials.
    if platform is not None:
        for s in f.specials:
            s.platform = platform
    f, lowered_specials = lower_specials(special_overrides, f)

    # Lower basics (for basics included in specials).
    f = lower_basics(f)

    # IOs collection (when not specified).
    if len(ios) == 0:
        assert platform is not None
        ios = platform.constraint_manager.get_io_signals()

    # IOs backtrace/naming.
    for io in sorted(ios, key=lambda x: x.duid):
        if io.name_override is None:
            io_name = io.backtrace[-1][0]
            if io_name:
                io.name_override = io_name

    # Build Signal Namespace.
    # ----------------------
    ns = build_signal_namespace(
        signals = (
            list_signals(f) |
            list_special_ios(f, ins=True, outs=True, inouts=True) |
            ios
        ),
        reserved_keywords = _ieee_1800_2017_verilog_reserved_keywords
    )
    ns.clock_domains = f.clock_domains

    # Build Verilog.
    # --------------
    verilog = ""

    # Banner.
    verilog += _generate_banner(
        filename = name,
        device   = getattr(platform, "device", "Unknown")
    )

    # Timescale.
    verilog += _generate_timescale(
        time_unit      = time_unit,
        time_precision = time_precision
    )

    # Module Definition.
    verilog += _generate_separator("Module")
    verilog += _generate_module(f, ios, name, ns, attr_translate)

    # Module Hierarchy.
    verilog += _generate_separator("Hierarchy")
    verilog += _generate_hierarchy(top=LiteXContext.top)

    # Module Signals.
    verilog += _generate_separator("Signals")
    verilog += _generate_signals(f, ios, name, ns, attr_translate, regs_init)

    # Combinatorial Logic.
    verilog += _generate_separator("Combinatorial Logic")
    if regular_comb:
        verilog += _generate_combinatorial_logic_synth(f, ns)
    else:
        verilog += _generate_combinatorial_logic_sim(f, ns)

    # Synchronous Logic.
    verilog += _generate_separator("Synchronous Logic")
    verilog += _generate_synchronous_logic(f, ns)

    # Specials
    verilog += _generate_separator("Specialized Logic")
    verilog += _generate_specials(
        name           = name,
        overrides      = special_overrides,
        specials       = f.specials - lowered_specials,
        namespace      = ns,
        add_data_file  = r.add_data_file,
        attr_translate = attr_translate
    )

    # Module End.
    verilog += "endmodule\n"

    # Trailer.
    verilog += _generate_trailer()

    r.set_main_source(verilog)
    r.ns = ns

    return r
