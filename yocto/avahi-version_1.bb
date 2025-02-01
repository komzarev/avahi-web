SUMMARY = "bitbake-layers recipe"
DESCRIPTION = "Recipe created by bitbake-layers"
LICENSE = "CLOSED"


SRC_URI += " file://avahi-version.service \
"

MY_BUILD_VERSION="42"
MY_APP_NAME="MyApp"

do_install_append() {
  
  install -d ${D}/etc/avahi/services
  install -m 0644 ${WORKDIR}/avahi-version.service ${D}/etc/avahi/services/avahi-version.service
  sed -i -e 's/VERSION/${MY_BUILD_VERSION}/g' ${D}/etc/avahi/services/avahi-version.service
  sed -i -e 's/APP_NAME/${MY_APP_NAME}/g' ${D}/etc/avahi/services/avahi-version.service
}
