<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <xsl:import href="/usr/share/xml/docbook/stylesheet/docbook-xsl/xhtml/chunk.xsl" />
    <xsl:param name="chunker.output.encoding" select="'utf-8'" />
    <xsl:param name="l10n.gentext.language" select="'zh_cn'" />
    <xsl:param name="html.stylesheet" select="'docbook.css'" />
    <xsl:param name="admon.graphics" select="1" />
    <!--<xsl:param name="base.dir" select="./html/" /> //-
    <xsl:param name="chunker.output.indent" select="yes" /> //-->
    <xsl:param name="section.autolabel" select="1" />
    <xsl:param name="section.label.includes.component.label" select="1" />
    <xsl:param name="table.borders.width.css" select="0" />
    <xsl:param name="bibliography.numbered" select="1" />
    <xsl:param name="toc.max.depth" select="2" />
    <xsl:param name="generate.section.toc.level" select="0" />
    <xsl:param name="toc.section.depth" select="2" />

    <xsl:param name="generate.toc">
        appendix            toc
        article/appendix    nop
        article             toc,title
        book                toc,title,example
        chapter             toc,title
        part                toc,title
        preface             toc,title
        qandadiv            toc
        qandaset            toc
        reference           toc,title
        sect1               toc
        sect2               toc
        sect3               toc
        sect4               toc
        sect5               toc
        section             toc
        set                 toc,title
    </xsl:param>

    <xsl:template match="processing-instruction('linebreak')"><br/></xsl:template>
</xsl:stylesheet>
