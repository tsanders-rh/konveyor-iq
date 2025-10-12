package org.eclipse.microprofile.config.inject;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Stub for MicroProfile @ConfigProperty annotation.
 * Used for compilation testing only.
 */
@Target({ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface ConfigProperty {
    String name();
    String defaultValue() default "";
}
