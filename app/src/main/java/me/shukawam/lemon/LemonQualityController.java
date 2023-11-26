package me.shukawam.lemon;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.oracle.bmc.aivision.model.AnalyzeImageResult;

import io.micronaut.http.annotation.Consumes;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.annotation.Produces;
import io.micronaut.http.multipart.StreamingFileUpload;
import io.micronaut.http.MediaType;
import jakarta.inject.Inject;

@Controller("/lemon")
public class LemonQualityController {
    private static final Logger logger = LoggerFactory.getLogger(LemonQualityController.class);
    private final LemonQualityService service;

    @Inject
    public LemonQualityController(LemonQualityService service) {
        this.service = service;
    }

    @Post("/check")
    @Consumes(MediaType.MULTIPART_FORM_DATA)
    @Produces(MediaType.APPLICATION_JSON)
    public AnalyzeImageResult checkLemonQuality(StreamingFileUpload file) {
        logger.info("Inside into LemonQualityController#checkLemonQuality");
        return service.analyzeImage(file);
    }

}
