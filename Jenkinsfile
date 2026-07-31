pipeline {
    agent { label 'python' }
    environment {
        // site specifics
        AUTHOR = "Ramon Garcia"
        ACCOUNT = "monfg"
        DOMAIN = "codeberg.org"
        SITE_NAME = "${ACCOUNT}.${DOMAIN}"
        SITE_TITLE = "${AUTHOR}'s blog"

        // build specifics
        SOURCE = "blog"
        SITE_DIR = "site"
        GIT_URL = "ssh://git@192.168.0.110:/home/git/projects/${SOURCE}.git"

        // Codeberg pages specifics
        SITE_PAGES = "page"
        SITE_PAGES_URL = "ssh://git@codeberg.org/${ACCOUNT}/${SITE_PAGES}.git"
        BASE_URL = "https://${ACCOUNT}.${DOMAIN}/${SITE_PAGES}/${SITE_DIR}"

        // neocities base url:  BASE_URL = "https://${ACCOUNT}.${DOMAIN}/${SITE_PAGES}

        TRACKING_URL = "https://${ACCOUNT}.goatcounter.com"
        LOCAL_BASE_URL = "http://127.0.0.1:2080"
        DEST = "../${SITE_DIR}"
        SRC = "../${SOURCE}"
        LOCAL_PATH_ROOT = "/opt/deploy"
        LOCAL_PATH = "${LOCAL_PATH_ROOT}/site"
        STABLE = "../last"

        // blog path specifics
        STATICS_IMG = ".ico,.webp"
        STATICS_ASSETS = ".css"

    }
    parameters {
        booleanParam(
            name: 'FORCE_SETUP',
            defaultValue: false,
            description: 'Force a fresh installation of uv and sync environment'
        )
        booleanParam(
            name: 'CLEAN_REPOSITORIES',
            defaultValue: false,
            description: 'Remove the repositories in the workspace'
        )
        booleanParam(
            name: 'LOCAL_VALIDATION',
            defaultValue: true,
            description: 'Execute a local deployment to validate results'
        )
        booleanParam(
            name: 'UPDATE_RSS',
            defaultValue: true,
            description: 'Update the RSS feed (only works for Posts)'
        )
    }
    stages {
        stage('Environment Setup') {
            steps {
                script {
                    if (!fileExists('/home/jenkins/.local/bin/uv') || params.FORCE_SETUP) {
                        sh '''
                            curl -LsSf https://astral.sh/uv/install.sh | sh
                            export PATH="$HOME/.local/bin:$PATH"
                            uv sync --frozen
                        '''
                    }
                }
            }
        }
    }
}
