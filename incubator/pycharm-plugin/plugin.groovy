import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.DumbAware

import static liveplugin.PluginUtil.registerAction
import static liveplugin.PluginUtil.show

import com.intellij.openapi.actionSystem.CommonDataKeys
import static liveplugin.PluginUtil.*
import com.intellij.openapi.wm.IdeFocusManager

registerAction("Hello World", "alt shift H") { AnActionEvent event ->
	def project = event?.project
    def editor = CommonDataKeys.EDITOR.getData(event.dataContext)
    if (project == null || editor == null) {
        show("No project or editor")
        return
    }

    def caretModel = editor.caretModel
    def document = editor.document

    def line_no = 10
    def col_no = 5

    if (document.lineCount >= line_no) {
        def lineStartOffset = document.getLineStartOffset(line_no-1)
        def lineEndOffset = document.getLineEndOffset(line_no-1)
        def targetOffset = Math.min(lineStartOffset + col_no, lineEndOffset)

        caretModel.moveToOffset(targetOffset)
        IdeFocusManager.getInstance(project).requestFocus(editor.contentComponent, true)
        def scrollingModel = editor.scrollingModel
        scrollingModel.scrollToCaret(com.intellij.openapi.editor.ScrollType.RELATIVE)
    }
    show("scrolled to ${line_no}:${col_no}")
}
if (!isIdeStartup)
show("Loaded 'Set caret and scroll to it'<br/>Use alt+shift+H to run it")
