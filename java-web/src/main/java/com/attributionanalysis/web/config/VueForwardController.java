package com.attributionanalysis.web.config;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class VueForwardController {

    @GetMapping("/")
    public String root() {
        return "redirect:/vue/";
    }

    @GetMapping("/vue")
    public String vueRoot() {
        return "redirect:/vue/";
    }

    @GetMapping("/vue/")
    public String vueIndex() {
        return "forward:/vue/index.html";
    }
}
