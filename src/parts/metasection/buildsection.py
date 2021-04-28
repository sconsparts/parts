# stage - prototype
from .metasection import MetaSection
from .phaseinfo import PhaseInfo
import parts.api.register as register


class Build(MetaSection):
    name = "build" # this is the declorator name
    # the first concept is the what all targets will map to
    # the values after this are mapped to build:: and can be given special actions
    concepts = ("build", "make", "construct")

    def __init__(self):
        super().__init__()

    def ConfigureSetup(self, callback):
        '''
        need custom setup for configure phases
        '''
        config = self.Env.Configure()
        callback(config)
        config.Finish()

    def ProcessSection(self, level):
        '''
        This function must be define to process and load the section logic correctly
        '''
        
        if self.isPhasesDefined("configure"):
            self.ProcessPhase("configure")
        if self.isPhasesDefined("config"):
            self.ProcessPhase("config")
        # ideally better logic here to fill in when stage is called
        if self.isPhasesDefined("source"):
            self.ProcessPhase("source")
        elif self.isPhasesDefined("sdk"):
            self.ProcessPhase("sdk")
        elif self.isPhasesDefined("system"):
            self.ProcessPhase("system")
        


register.add_section(
    metasection=Build,
    phases=[
        # this allows for per part configure logic
        # is where one can set flags or values that would control build items
        PhaseInfo(
            name="configure",
            setup_func=Build.ConfigureSetup,
            optional=True
        ),
        # called to do general environment setup
        # set flags, etc.. differs from configure as it more about setting
        # vs state checks that can be more expensive to do
        PhaseInfo(
            name="config",
            optional=True
        ),
        # called when building from source
        # if not defined will backup to SDK logic
        PhaseInfo(
            name="source",
            alt_names=["build"],
            optional=True
        ),
        # called to use some sort of SDK prebuilds
        # generally only needs to export values/properties that should
        # shared with dependents
        PhaseInfo(
            name="sdk",
            optional=True
        ),
        # ??
        # called to export value to build from a system installed items
        PhaseInfo(
            name="system",
            optional=True
        ),
    ]
)
