from typing import Optional
import antlr4

from thrifty.parser.ThriftListener import ThriftListener
from thrifty.parser.ThriftLexer import ThriftLexer
from thrifty.model import \
    ThriftyFile, \
    ThriftyService, \
    IFileItem, \
    ThriftyStruct, \
    ThriftyException, \
    ThriftyEnum
from thrifty.model.comment_parser import comment_text
from thrifty.parser.ThriftParser import ThriftParser


class FileLoader(ThriftListener):
    """
    Loads a Thrifty model from an AST tree.
    """

    def __init__(self, name: str) -> None:
        self.thrifty_file = ThriftyFile(name)
        self.current_file_item: Optional[IFileItem] = None
        self.current_comment: Optional[str] = None

    def enterEnum_rule(self, ctx: ThriftParser.Enum_ruleContext):
        self.current_file_item = ThriftyEnum(str(ctx.IDENTIFIER()))
        self.thrifty_file.file_items.append(self.current_file_item)

    def exitEnum_rule(self, ctx: ThriftParser.Enum_ruleContext):
        self.current_file_item = None

    def enterService(self, ctx: ThriftParser.ServiceContext):
        self.current_file_item = ThriftyService(str(ctx.IDENTIFIER()))
        self.thrifty_file.file_items.append(self.current_file_item)

    def exitService(self, ctx: ThriftParser.ServiceContext):
        self.current_file_item = None

    def enterStruct(self, ctx: ThriftParser.StructContext):
        self.current_file_item = ThriftyStruct(str(ctx.IDENTIFIER()))
        self.thrifty_file.file_items.append(self.current_file_item)

    def exitStruct(self, ctx: ThriftParser.StructContext):
        self.current_file_item = None

    def enterException(self, ctx: ThriftParser.ExceptionContext):
        self.current_file_item = ThriftyException(str(ctx.IDENTIFIER()))
        self.thrifty_file.file_items.append(self.current_file_item)

    def exitException(self, ctx: ThriftParser.ExceptionContext):
        self.current_file_item = None

    def enterField(self, ctx: ThriftParser.FieldContext):
        pass

    def enterFunction(self, ctx: ThriftParser.FunctionContext):
        pass

    def enterDocument(self, ctx: ThriftParser.DocumentContext):
        pass

    def exitDocument(self, ctx: ThriftParser.DocumentContext):
        pass

    def enterComment_singleline(self, ctx: ThriftParser.Comment_singlelineContext):
        pass

    def enterComment_multiline(self, ctx: ThriftParser.Comment_multilineContext):
        self.current_comment = comment_text(ctx.ML_COMMENT().getText())


def load_model_from_file(file_name: str) -> ThriftyFile:
    with open(file_name, 'r', encoding='utf-8') as f:
        lexer = ThriftLexer(antlr4.InputStream(f.read()))

    token_stream = antlr4.CommonTokenStream(lexer)

    parser = ThriftParser(token_stream)

    tree_walker = antlr4.ParseTreeWalker()

    file_loader = FileLoader(name=file_name)
    tree_walker.walk(file_loader, parser.document())

    model = file_loader.thrifty_file

    return model

