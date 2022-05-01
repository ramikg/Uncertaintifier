import ida_idaapi
import ida_hexrays
import ida_kernwin

REGISTER_CONTEXT_MENU_ITEMS = True

INC_ACTION_NAME = INC_ACTION_DESCRIPTION = 'Increase uncertainty'
INC_ACTION_HOTKEY = 'Ctrl-/'
DEC_ACTION_NAME = DEC_ACTION_DESCRIPTION = 'Decrease uncertainty'
DEC_ACTION_HOTKEY = 'Ctrl-Alt-/'


class UncertaintifierFailedGettingVariableNameError(Exception):
    pass


def _get_lvar(widget):
    vdui = ida_hexrays.get_widget_vdui(widget)
    return vdui.item.get_lvar()


def _is_pseudocode_lvar(widget):
    if ida_kernwin.get_widget_type(widget) != ida_kernwin.BWN_PSEUDOCODE:
        return False

    return _get_lvar(widget) is not None


class QuestionMarkAdderRemover(ida_kernwin.action_handler_t):
    QUESTION_MARK = '?'

    def update(self, ctx):
        if self._should_enable_action(ctx):
            return ida_kernwin.AST_ENABLE
        else:
            return ida_kernwin.AST_DISABLE

    def _should_enable_action(self, ctx):
        return _is_pseudocode_lvar(ctx.widget)

    @staticmethod
    def _get_lvar_name(ctx):
        try:
            return _get_lvar(ctx.widget).name
        except AttributeError:
            print('Failed getting highlighted variable name. Please try again.')
            raise UncertaintifierFailedGettingVariableNameError()

    @staticmethod
    def _rename_lvar(ctx, new_name):
        IDAAPI_RENAME_LVAR_IS_USER_NAME = 1

        lvar = _get_lvar(ctx.widget)
        vdui = ida_hexrays.get_widget_vdui(ctx.widget)

        vdui.rename_lvar(lvar, new_name, IDAAPI_RENAME_LVAR_IS_USER_NAME)


class QuestionMarkAdder(QuestionMarkAdderRemover):
    def activate(self, ctx):
        try:
            old_name = self._get_lvar_name(ctx)
        except UncertaintifierFailedGettingVariableNameError:
            return

        self._rename_lvar(ctx, old_name + self.QUESTION_MARK)


class QuestionMarkRemover(QuestionMarkAdderRemover):
    def activate(self, ctx):
        try:
            old_name = self._get_lvar_name(ctx)
        except UncertaintifierFailedGettingVariableNameError:
            return

        assert old_name.endswith(self.QUESTION_MARK)
        self._rename_lvar(ctx, old_name[:-1])

    def _should_enable_action(self, ctx):
        # super() not used for Python 2 compatibility
        if not super(type(self), self)._should_enable_action(ctx):
            return False

        old_name = _get_lvar(ctx.widget).name
        return old_name.endswith(self.QUESTION_MARK)


class ContextMenuHooks(ida_kernwin.UI_Hooks):
    def finish_populating_widget_popup(self, widget, popup):
        if _is_pseudocode_lvar(widget):
            ida_kernwin.attach_action_to_popup(widget, popup, INC_ACTION_NAME, None)
            ida_kernwin.attach_action_to_popup(widget, popup, DEC_ACTION_NAME, None)


class Uncertaintifier(ida_idaapi.plugin_t):
    flags = ida_idaapi.PLUGIN_HIDE
    comment = 'Uncertaintifier'
    help = ''
    wanted_name = 'Uncertaintifier'
    wanted_hotkey = ''

    _hooks = ContextMenuHooks()

    def init(self):
        question_mark_adder_desc = ida_kernwin.action_desc_t(INC_ACTION_NAME,
                                                             INC_ACTION_DESCRIPTION,
                                                             QuestionMarkAdder(),
                                                             INC_ACTION_HOTKEY)
        question_mark_remover_desc = ida_kernwin.action_desc_t(DEC_ACTION_NAME,
                                                               DEC_ACTION_DESCRIPTION,
                                                               QuestionMarkRemover(),
                                                               DEC_ACTION_HOTKEY)

        ida_kernwin.register_action(question_mark_adder_desc)
        ida_kernwin.register_action(question_mark_remover_desc)

        if REGISTER_CONTEXT_MENU_ITEMS:
            self._hooks.hook()

        return ida_idaapi.PLUGIN_KEEP

    def run(self):
        pass

    def term(self):
        pass


def PLUGIN_ENTRY():
    return Uncertaintifier()
