package org.eclipse.microprofile.config;

import java.util.Optional;

/**
 * Stub for MicroProfile Config interface.
 * Used for compilation testing only.
 */
public interface Config {
    <T> T getValue(String propertyName, Class<T> propertyType);
    <T> Optional<T> getOptionalValue(String propertyName, Class<T> propertyType);
    Iterable<String> getPropertyNames();
    Iterable<ConfigSource> getConfigSources();
}
