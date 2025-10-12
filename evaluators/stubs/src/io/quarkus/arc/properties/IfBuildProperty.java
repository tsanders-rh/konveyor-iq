package io.quarkus.arc.properties;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Stub for Quarkus @IfBuildProperty annotation.
 * Used for compilation testing only.
 */
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
public @interface IfBuildProperty {
    String name();
    String stringValue() default "";
    boolean enableIfMissing() default false;
}
