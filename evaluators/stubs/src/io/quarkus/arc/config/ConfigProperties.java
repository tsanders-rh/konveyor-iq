package io.quarkus.arc.config;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Stub for Quarkus @ConfigProperties annotation.
 * Used for compilation testing only.
 */
@Target({ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface ConfigProperties {
    String prefix() default "";
    NamingStrategy namingStrategy() default NamingStrategy.KEBAB_CASE;

    enum NamingStrategy {
        KEBAB_CASE,
        VERBATIM
    }
}
