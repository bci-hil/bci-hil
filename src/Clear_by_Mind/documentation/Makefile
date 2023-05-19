all: clear_by_mind_hardware_schematic.pdf clear_by_mind_flow.pdf

clear_by_mind_hardware_schematic.pdf: clear_by_mind_hardware_schematic.dot
	dot -T pdf $< > $@
	dot -T eps $< > $<.eps

clear_by_mind_flow.pdf: clear_by_mind_flow.dot
	dot -T pdf $< > $@
	dot -T eps $< > $<.eps
