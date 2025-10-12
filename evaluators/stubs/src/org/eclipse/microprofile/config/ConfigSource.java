package org.eclipse.microprofile.config;

import java.util.Map;

/**
 * Stub for MicroProfile ConfigSource interface.
 * Used for compilation testing only.
 */
public interface ConfigSource {
    Map<String, String> getProperties();
    String getValue(String propertyName);
    String getName();
    int getOrdinal();
}
