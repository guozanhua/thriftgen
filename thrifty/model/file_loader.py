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
    ThriftyEnum, \
    IAttributeHolder, \
    ThriftyAttribute, \
    ThriftyType, \
    ThriftyMethod, \
    ThrowsHolder
from thrifty.model.comment_parser import comment_text
from thrifty.parser.ThriftParser import ThriftParser


class FileLoader(ThriftListener):
    """
    Loads a Thrifty model from an AST tree.
    """

    def __init__(self, name: str) -> None:
        self.thrifty_file = ThriftyFile(name)
        # The current_file_item is different than the attribute holder, since
        # in the case of services, the functions are the ones having the
        # attributes, while the current_file_item is still the service.
        self.current_file_item: Optional[IFileItem] = None
        self.attribute_holder: IAttributeHolder = None
        self.current_comment: Optional[str] = None

    def enterEnum_rule(self, ctx: ThriftParser.Enum_ruleContext):
        self.current_file_item = ThriftyEnum(str(ctx.IDENTIFIER()))
        self.attribute_holder = self.current_file_item
        self.thrifty_file.file_items.append(self.current_file_item)

        if self.current_comment:
            self.current_file_item.comment = self.current_comment
            self.current_comment = None

    def exitEnum_rule(self, ctx: ThriftParser.Enum_ruleContext):
        self.attribute_holder = None
        self.current_file_item = None

    def enterEnum_field(self, ctx:ThriftParser.Enum_fieldContext):
        assert isinstance(self.current_file_item, ThriftyEnum)
        self.current_file_item.values.append(str(ctx.IDENTIFIER()))

    def enterService(self, ctx: ThriftParser.ServiceContext):
        self.current_file_item = ThriftyService(str(ctx.IDENTIFIER(0)))
        self.thrifty_file.file_items.append(self.current_file_item)

    def exitService(self, ctx: ThriftParser.ServiceContext):
        self.current_file_item = None

    def enterStruct(self, ctx: ThriftParser.StructContext):
        self.current_file_item = ThriftyStruct(str(ctx.IDENTIFIER()))
        self.attribute_holder = self.current_file_item
        self.thrifty_file.file_items.append(self.current_file_item)

        if self.current_comment:
            self.current_file_item.comment = self.current_comment
            self.current_comment = None

    def exitStruct(self, ctx: ThriftParser.StructContext):
        self.current_file_item = None
        self.attribute_holder = None

    def enterException(self, ctx: ThriftParser.ExceptionContext):
        self.current_file_item = ThriftyException(str(ctx.IDENTIFIER()))
        self.attribute_holder = self.current_file_item
        self.thrifty_file.file_items.append(self.current_file_item)

    def exitException(self, ctx: ThriftParser.ExceptionContext):
        self.current_file_item = None
        self.attribute_holder = None

    def enterField(self, ctx: ThriftParser.FieldContext):
        # FIXME: this should be the correct way
        # assert isinstance(self.attribute_holder, IAttributeHolder)
        if not isinstance(self.attribute_holder, IAttributeHolder):
            return
        # end FIXME

        field_type = ctx.field_type()
        attribute = ThriftyAttribute(str(ctx.IDENTIFIER()),
                                     ThriftyType(field_type.getText()))

        if self.current_comment:
            attribute.comment = self.current_comment
            self.current_comment = None

        self.attribute_holder.attributes.append(attribute)

    def enterFunction(self, ctx: ThriftParser.FunctionContext):
        print("enter function")
        service: ThriftyService = self.current_file_item
        assert service

        method = ThriftyMethod(str(ctx.IDENTIFIER()))

        if self.current_comment:
            method.comment = self.current_comment
            self.current_comment = None

        method.return_type = ThriftyType(ctx.function_type().getText())
        self.attribute_holder = method
        service.methods.append(method)

    def exitFunction(self, ctx: ThriftParser.FunctionContext):
        self.attribute_holder = None

    def enterThrows_list(self, ctx:ThriftParser.Throws_listContext):
        method: ThriftyMethod = self.attribute_holder
        self.attribute_holder = ThrowsHolder(method.exceptions)

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

