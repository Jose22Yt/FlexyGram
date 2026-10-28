"""P11 inactive scaffolding only for legacy fallback probes; reveal_probe executes the active native route."""
def seed_fields(source):
 a=source.index('    private boolean instantRevealSeed, instantRevealContainerWidth;');b=source.index('    private void clearInstantRevealSeed()',a)
 return source[a:b].replace('private ','')
