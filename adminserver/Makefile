OBJS     = all
SRCS     = ./pxml/mainbook.xml
PARAM    = param.xsl
ARGS     = --output phtml/
COMPILER = xsltproc

$(OBJS):$(SRCS) $(PARAM)
	$(COMPILER) $(ARGS) $(PARAM) $(SRCS)

clean:
	rm -rf ./phtml/*.html
